# API routes package

from app.api.auth import router as auth_router
from app.api.projects import router as projects_router

__all__ = ["auth_router", "projects_router"]
