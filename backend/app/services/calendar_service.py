"""
Service untuk integrasi Google Calendar.
Menangani fetch events dan mapping ke activity log.
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

import httpx

from app.core.config import settings
from app.schemas.calendar import CalendarEventResponse

logger = logging.getLogger(__name__)

# Konstanta Google Calendar API
GCAL_API_BASE = "https://www.googleapis.com/calendar/v3"
GCAL_EVENTS_ENDPOINT = f"{GCAL_API_BASE}/calendars/primary/events"
GCAL_TIMEOUT_SECONDS = 15
GCAL_MAX_EVENTS = 200
GCAL_DATE_RANGE_DAYS = 7  # 7 hari lalu + 7 hari depan

# Durasi default untuk all-day events (dalam jam)
ALL_DAY_DURATION_HOURS = Decimal("8.00")


class CalendarServiceError(Exception):
    """Base exception untuk CalendarService."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class CalendarTimeoutError(CalendarServiceError):
    """Error saat Google Calendar API timeout (> 15s)."""

    def __init__(self):
        super().__init__("Google Calendar API timeout")


class CalendarAPIError(CalendarServiceError):
    """Error dari Google Calendar API (non-timeout)."""

    def __init__(self, message: str):
        super().__init__(message)


class CalendarService:
    """
    Service utama untuk interaksi dengan Google Calendar API.
    Menggunakan httpx async client dengan timeout 15 detik.
    """

    async def fetch_events(self, access_token: str) -> list[CalendarEventResponse]:
        """
        Fetch events dari Google Calendar primary calendar.
        Range: 7 hari lalu sampai 7 hari depan, max 200 events.

        Args:
            access_token: Google OAuth access token user.

        Returns:
            List CalendarEventResponse berisi events yang ditemukan.

        Raises:
            CalendarTimeoutError: Jika API tidak merespons dalam 15 detik.
            CalendarAPIError: Jika API mengembalikan error.
        """
        now = datetime.now(timezone.utc)
        time_min = (now - timedelta(days=GCAL_DATE_RANGE_DAYS)).isoformat()
        time_max = (now + timedelta(days=GCAL_DATE_RANGE_DAYS)).isoformat()

        params = {
            "timeMin": time_min,
            "timeMax": time_max,
            "maxResults": GCAL_MAX_EVENTS,
            "singleEvents": "true",
            "orderBy": "startTime",
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(GCAL_TIMEOUT_SECONDS)
            ) as client:
                response = await client.get(
                    GCAL_EVENTS_ENDPOINT,
                    params=params,
                    headers=headers,
                )
        except httpx.TimeoutException:
            logger.error("Google Calendar API timeout setelah 15 detik")
            raise CalendarTimeoutError()
        except httpx.RequestError as e:
            logger.error(f"Google Calendar API request error: {e}")
            raise CalendarAPIError(f"Gagal menghubungi Google Calendar: {str(e)}")

        # Handle non-200 response
        if response.status_code != 200:
            error_detail = response.text[:200]
            logger.error(
                f"Google Calendar API error {response.status_code}: {error_detail}"
            )
            raise CalendarAPIError(
                f"Google Calendar API error ({response.status_code}): {error_detail}"
            )

        # Parse response
        data = response.json()
        items = data.get("items", [])

        events: list[CalendarEventResponse] = []
        for item in items:
            event = self._parse_event(item)
            if event:
                events.append(event)

        logger.info(f"Berhasil fetch {len(events)} events dari Google Calendar")
        return events

    def _parse_event(self, item: dict) -> Optional[CalendarEventResponse]:
        """
        Parse satu item event dari Google Calendar API response.
        Menentukan apakah event all-day dan menghitung durasi.
        """
        event_id = item.get("id")
        title = item.get("summary", "(No Title)")

        if not event_id:
            return None

        start_raw = item.get("start", {})
        end_raw = item.get("end", {})
        description = item.get("description")

        # Deteksi all-day event (menggunakan "date" bukan "dateTime")
        is_all_day = "date" in start_raw and "dateTime" not in start_raw

        if is_all_day:
            # All-day event: durasi default 8 jam
            duration_hours = ALL_DAY_DURATION_HOURS
            start_str = start_raw.get("date")
            end_str = end_raw.get("date")
        else:
            # Timed event: hitung durasi dari start dan end
            start_str = start_raw.get("dateTime")
            end_str = end_raw.get("dateTime")
            duration_hours = self._calculate_duration(start_str, end_str)

        return CalendarEventResponse(
            gcal_event_id=event_id,
            title=title,
            start=start_str,
            end=end_str,
            duration_hours=duration_hours,
            is_all_day=is_all_day,
            description=description,
        )

    def _calculate_duration(
        self, start_str: Optional[str], end_str: Optional[str]
    ) -> Decimal:
        """
        Hitung durasi dalam jam dari string datetime ISO.
        Minimum 0.25 jam (15 menit), maksimum 24 jam.
        """
        if not start_str or not end_str:
            # Fallback ke 1 jam jika data tidak lengkap
            return Decimal("1.00")

        try:
            start_dt = datetime.fromisoformat(start_str)
            end_dt = datetime.fromisoformat(end_str)
            delta = end_dt - start_dt
            hours = Decimal(str(delta.total_seconds())) / Decimal("3600")

            # Clamp ke range valid
            hours = max(Decimal("0.25"), min(hours, Decimal("24.00")))
            # Bulatkan ke 2 desimal
            return hours.quantize(Decimal("0.01"))
        except (ValueError, TypeError) as e:
            logger.warning(f"Gagal parse durasi event: {e}")
            return Decimal("1.00")

    @staticmethod
    def generate_notes(title: str, description: Optional[str] = None) -> str:
        """
        Auto-generate raw_notes dari event title dan description.
        Format: "[Calendar] {title}" atau "[Calendar] {title} — {description}"
        """
        if description:
            # Potong description jika terlalu panjang
            desc_trimmed = description[:500] if len(description) > 500 else description
            return f"[Calendar] {title} — {desc_trimmed}"
        return f"[Calendar] {title}"


# Singleton instance
calendar_service = CalendarService()
