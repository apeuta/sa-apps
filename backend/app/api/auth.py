"""
API endpoints untuk autentikasi Google OAuth 2.0.
Menangani login, callback, refresh token, logout, get current user, dan demo login.
"""

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginResponse,
    OAuthError,
    RefreshRequest,
    TokenPair,
    UserResponse,
)
from app.services.auth_service import (
    AuthServiceError,
    DomainNotAllowedError,
    OAuthError as ServiceOAuthError,
    TokenError,
    auth_service,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# === Demo Mode ===
# Konfigurasi demo users — setiap role punya email dan nama tetap
DEMO_USERS = {
    "Sales": {
        "email": "demo-sales@portal-sa.local",
        "name": "Demo Sales",
        "google_id": "demo-google-id-sales",
    },
    "SA": {
        "email": "demo-sa@portal-sa.local",
        "name": "Demo SA",
        "google_id": "demo-google-id-sa",
    },
    "Lead_SA": {
        "email": "demo-lead@portal-sa.local",
        "name": "Demo Lead SA",
        "google_id": "demo-google-id-lead-sa",
    },
    "Admin": {
        "email": "demo-admin@portal-sa.local",
        "name": "Demo Admin",
        "google_id": "demo-google-id-admin",
    },
}


class DemoLoginRequest(BaseModel):
    """Request body untuk demo login."""
    role: Literal["Sales", "SA", "Lead_SA", "Admin"]


@router.post("/demo-login", summary="Demo Login (bypass OAuth)")
async def demo_login(
    body: DemoLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login tanpa Google OAuth untuk development/demo.
    Hanya aktif jika DEMO_MODE=true di environment.
    Membuat demo user di database jika belum ada (INSERT IF NOT EXISTS).
    Mengembalikan JWT token yang identik formatnya dengan OAuth flow.
    """
    # Cek apakah demo mode aktif
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=403,
            detail="Demo mode tidak aktif. Gunakan Google OAuth untuk login.",
        )

    # Ambil konfigurasi demo user berdasarkan role
    demo_config = DEMO_USERS[body.role]

    # Cari user di database berdasarkan email (INSERT IF NOT EXISTS)
    stmt = select(User).where(User.email == demo_config["email"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # Buat demo user baru di database
        user = User(
            id=uuid.uuid4(),
            email=demo_config["email"],
            name=demo_config["name"],
            role=body.role,
            google_id=demo_config["google_id"],
            avatar_url=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Generate JWT token pair — menggunakan method yang sama dengan OAuth flow
    tokens = auth_service._create_token_pair(user)

    return LoginResponse(
        user=UserResponse.model_validate(user),
        tokens=tokens,
    )


def _get_token_from_header(request: Request) -> str:
    """Ekstrak Bearer token dari Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization header tidak ditemukan atau format salah.",
        )
    return auth_header[7:]  # Hapus "Bearer " prefix


@router.get("/login", summary="Initiate Google OAuth Login")
async def login(redirect_url: str = Query(default=None, description="URL redirect setelah login")):
    """
    Memulai OAuth flow dengan redirect ke Google consent screen.
    Client akan di-redirect ke Google untuk login.
    """
    # Gunakan redirect_url sebagai state (opsional)
    oauth_url = auth_service.initiate_oauth(state=redirect_url)
    return RedirectResponse(url=oauth_url)


@router.get("/callback", summary="Handle Google OAuth Callback")
async def callback(
    code: str = Query(default=None, description="Authorization code dari Google"),
    error: str = Query(default=None, description="Error dari Google jika consent dibatalkan"),
    state: str = Query(default=None, description="State parameter (redirect URL)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle callback dari Google setelah user melakukan consent.
    Memproses authorization code, validasi domain, dan buat session.
    """
    # Handle jika user membatalkan consent
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"Login dibatalkan oleh user: {error}",
        )

    if not code:
        raise HTTPException(
            status_code=400,
            detail="Authorization code tidak ditemukan.",
        )

    try:
        user, tokens = await auth_service.handle_callback(code, db)
    except DomainNotAllowedError as e:
        raise HTTPException(status_code=403, detail=e.detail)
    except ServiceOAuthError as e:
        raise HTTPException(status_code=502, detail=e.detail)
    except AuthServiceError as e:
        raise HTTPException(status_code=400, detail=e.detail)

    return LoginResponse(
        user=UserResponse.model_validate(user),
        tokens=tokens,
    )


@router.post("/refresh", summary="Refresh Access Token", response_model=TokenPair)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token menggunakan refresh token yang masih valid.
    Mengembalikan token pair baru (access + refresh).
    """
    try:
        tokens = await auth_service.refresh_token(body.refresh_token, db)
    except TokenError as e:
        raise HTTPException(status_code=401, detail=e.detail)

    return tokens


@router.post("/logout", summary="Logout / Revoke Session")
async def logout(request: Request):
    """
    Revoke session user (logout).
    Client harus menghapus token dari storage setelah endpoint ini dipanggil.
    """
    token = _get_token_from_header(request)

    try:
        auth_service.revoke_session(token)
    except TokenError as e:
        raise HTTPException(status_code=401, detail=e.detail)

    return {"message": "Logout berhasil."}


@router.get("/me", summary="Get Current User", response_model=UserResponse)
async def get_me(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Ambil informasi user yang sedang login berdasarkan access token.
    Endpoint ini juga berfungsi sebagai validasi session aktif.
    """
    token = _get_token_from_header(request)

    try:
        user = await auth_service.get_current_user(token, db)
    except TokenError as e:
        raise HTTPException(status_code=401, detail=e.detail)

    return UserResponse.model_validate(user)
