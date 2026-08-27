"""
Konfigurasi koneksi database menggunakan SQLAlchemy async engine.
Menyediakan session factory dan fungsi pengecekan kesehatan database.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.core.config import settings


# Buat async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class untuk semua SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency untuk mendapatkan database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_health() -> bool:
    """
    Cek kesehatan koneksi database.
    Return True jika database bisa diakses, False jika tidak.
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False
