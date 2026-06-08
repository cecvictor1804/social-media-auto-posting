"""Timezone helpers. DB stores UTC; the UI works in DISPLAY_TIMEZONE."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.config import settings


def _display_tz() -> ZoneInfo:
    try:
        return ZoneInfo(settings.display_timezone)
    except Exception:
        return ZoneInfo("UTC")


def local_to_utc(naive_local: datetime) -> datetime:
    """Interpret a naive datetime as DISPLAY_TIMEZONE and convert to UTC."""
    return naive_local.replace(tzinfo=_display_tz()).astimezone(timezone.utc)


def utc_to_local_str(dt: datetime | None, fmt: str = "%Y-%m-%d %H:%M") -> str:
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_display_tz()).strftime(fmt)


def parse_local_input(value: str) -> datetime:
    """Parse an <input type=datetime-local> value (YYYY-MM-DDTHH:MM) to UTC."""
    naive = datetime.strptime(value, "%Y-%m-%dT%H:%M")
    return local_to_utc(naive)
