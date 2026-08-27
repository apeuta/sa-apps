"""
API endpoints untuk autentikasi Google OAuth 2.0.
Menangani login, callback, refresh token, logout, dan get current user.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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
