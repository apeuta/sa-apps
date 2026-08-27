"""
Rate limiter sederhana menggunakan in-memory storage.
Membatasi 100 request per menit per user (berdasarkan authenticated user ID).
Untuk production, bisa diganti dengan Redis-based rate limiter.
"""

import time
from collections import defaultdict
from typing import Dict, List

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Middleware rate limiter yang membatasi jumlah request per user per menit.
    Menggunakan sliding window algorithm sederhana dengan in-memory storage.
    """

    def __init__(self, app, max_requests: int = None):
        super().__init__(app)
        self.max_requests = max_requests or settings.RATE_LIMIT_PER_MINUTE
        self.window_seconds = 60  # 1 menit
        # Menyimpan timestamp request per user: {user_id: [timestamps]}
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def _get_user_identifier(self, request: Request) -> str:
        """
        Dapatkan identifier user dari request.
        Prioritas: authenticated user ID > IP address.
        """
        # Cek apakah ada user_id dari auth middleware
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fallback ke IP address untuk request yang belum terautentikasi
        client_host = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_host = forwarded_for.split(",")[0].strip()
        return f"ip:{client_host}"

    def _cleanup_old_requests(self, user_id: str, now: float):
        """Hapus timestamp request yang sudah di luar window."""
        cutoff = now - self.window_seconds
        self._requests[user_id] = [
            ts for ts in self._requests[user_id] if ts > cutoff
        ]

    def _calculate_retry_after(self, user_id: str, now: float) -> int:
        """Hitung jumlah detik sebelum user bisa request lagi."""
        if not self._requests[user_id]:
            return 0
        oldest_in_window = self._requests[user_id][0]
        retry_after = int(oldest_in_window + self.window_seconds - now) + 1
        return max(retry_after, 1)

    async def dispatch(self, request: Request, call_next):
        """Proses setiap request dan terapkan rate limiting."""
        # Skip rate limiting untuk health check dan docs
        skip_paths = ["/health", "/docs", "/redoc", "/openapi.json"]
        if request.url.path in skip_paths:
            return await call_next(request)

        now = time.time()
        user_id = self._get_user_identifier(request)

        # Bersihkan request lama
        self._cleanup_old_requests(user_id, now)

        # Cek apakah melebihi limit
        if len(self._requests[user_id]) >= self.max_requests:
            retry_after = self._calculate_retry_after(user_id, now)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "status": "error",
                    "data": None,
                    "message": f"Rate limit exceeded. Maksimal {self.max_requests} request per menit.",
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Catat request ini
        self._requests[user_id].append(now)

        # Lanjutkan ke handler berikutnya
        response = await call_next(request)
        return response
