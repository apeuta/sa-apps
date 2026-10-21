"""
SLA Scheduler — background scheduler internal ringan untuk Flow 2.

Menjalankan `sla_timer.process_sla_actions()` secara periodik sejak backend
naik, sehingga reminder H+3, eskalasi H+5, dan auto-lock folder Solutions
berjalan otomatis berbasis waktu tanpa trigger manual. Endpoint manual
`POST /sla/process` tetap berfungsi berdampingan.

Keputusan desain: ADR 0003 (docs/adr/0003-sla-internal-scheduler-for-mvp.md).

-----------------------------------------------------------------------------
BATAS MULTI-INSTANCE (WAJIB DIPERHATIKAN):
Scheduler ini TIDAK aman saat backend di-scale multi-instance. Setiap instance
akan menjalankan loop-nya sendiri dan MENDUPLIKASI aksi SLA (reminder/eskalasi/
lock bisa terpicu berkali-kali). Pilihan ini sengaja diambil untuk MVP
single-instance karena sederhana dan tanpa dependency infra tambahan. Saat
scale-out, ganti dengan cron eksternal yang memanggil `POST /sla/process`, atau
tambahkan leader-election agar hanya satu instance yang menjalankan scheduler.
-----------------------------------------------------------------------------
"""

import asyncio
import logging
from typing import Optional

from app.services.sla_timer import sla_timer

logger = logging.getLogger(__name__)


class SLAScheduler:
    """
    Background scheduler yang memanggil `process_sla_actions()` secara periodik.

    Jalan sebagai satu asyncio Task di event loop backend. Loop-nya tahan error:
    kegagalan satu iterasi di-log dan loop tetap lanjut ke interval berikutnya,
    sehingga scheduler tidak mati gara-gara satu error transient.
    """

    def __init__(self, interval_seconds: int) -> None:
        self.interval_seconds = interval_seconds
        self._task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        """True jika task scheduler sedang berjalan."""
        return self._task is not None and not self._task.done()

    def start(self) -> None:
        """
        Mulai loop scheduler sebagai background task.

        Idempoten: jika sudah berjalan, panggilan ulang tidak membuat task baru.
        """
        if self.is_running:
            logger.info("SLA scheduler sudah berjalan, skip start.")
            return

        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "SLA scheduler dimulai (interval %ss). "
            "CATATAN: tidak aman untuk multi-instance (lihat ADR 0003).",
            self.interval_seconds,
        )

    async def stop(self) -> None:
        """Hentikan loop scheduler dengan rapi (cancel + tunggu task selesai)."""
        if self._task is None:
            return

        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

        logger.info("SLA scheduler dihentikan.")

    async def _run_loop(self) -> None:
        """
        Loop utama: panggil `process_sla_actions()` lalu tidur selama interval.

        Error per-iterasi ditangkap dan di-log agar loop tetap hidup.
        `CancelledError` diteruskan agar `stop()` bisa menghentikan loop.
        """
        while True:
            try:
                await sla_timer.process_sla_actions()
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 — loop harus tahan error transient
                logger.exception("SLA scheduler gagal memproses aksi SLA; loop lanjut.")

            await asyncio.sleep(self.interval_seconds)
