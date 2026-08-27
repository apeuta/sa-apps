"""
Pydantic schemas untuk SLA Timer API responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SLAStatusResponse(BaseModel):
    """Response schema untuk status SLA proyek."""

    project_id: str
    status: str  # green, yellow, red
    days_elapsed: int
    is_locked: bool
    is_active: bool
    started_at: str
    stopped_at: Optional[str] = None


class SLAProcessingStats(BaseModel):
    """Response schema untuk hasil SLA processing."""

    total_checked: int
    reminders_sent: int
    escalations_sent: int
    locks_performed: int
    errors: list[str] = []
