"""
Date and time utilities for DMLClean.

Provides date parsing, formatting, and relative date helpers.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from loguru import logger

from dmlclean.constants.formats import DATE_FORMATS, RELATIVE_DATE_KEYWORDS


def parse_date(date_str: str) -> datetime | None:
    """
    Parse a date string into a datetime object.

    Supports multiple formats:
    - ISO date: 2025-01-01
    - EU date: 01/01/2025
    - ISO datetime: 2025-01-01T00:00:00
    - Human datetime: 2025-01-01 00:00:00
    - Relative keywords: today, yesterday, last_week, last_month, last_year

    Args:
        date_str: Date string to parse.

    Returns:
        datetime | None: Parsed datetime or None if parsing fails.
    """
    date_str = date_str.strip().lower()

    # Check for relative keywords
    if date_str in RELATIVE_DATE_KEYWORDS:
        days_ago = RELATIVE_DATE_KEYWORDS[date_str]
        result = datetime.now() - timedelta(days=days_ago)
        logger.debug(f"Parsed relative date '{date_str}' -> {result}")
        return result

    # Try each supported format
    for fmt in DATE_FORMATS:
        try:
            result = datetime.strptime(date_str, fmt)
            logger.debug(f"Parsed date '{date_str}' with format '{fmt}' -> {result}")
            return result
        except ValueError:
            continue

    # Try natural language parsing (if available)
    try:
        import parsedatetime

        cal = parsedatetime.Calendar()
        time_struct, parse_status = cal.parse(date_str)
        if parse_status:
            result = datetime(*time_struct[:6])
            logger.debug(f"Parsed natural language date '{date_str}' -> {result}")
            return result
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Natural language parsing failed: {e}")

    logger.warning(f"Failed to parse date: {date_str}")
    return None


def format_date(dt: datetime, format_str: str = "%Y-%m-%d") -> str:
    """
    Format a datetime object to string.

    Args:
        dt: Datetime to format.
        format_str: Format string (default: ISO date).

    Returns:
        str: Formatted date string.
    """
    return dt.strftime(format_str)


def format_datetime_relative(dt: datetime) -> str:
    """
    Format a datetime as relative time (e.g., "2 hours ago", "yesterday").

    Args:
        dt: Datetime to format.

    Returns:
        str: Human-readable relative time string.
    """
    now = datetime.now()
    diff = now - dt

    seconds = diff.total_seconds()
    minutes = seconds / 60
    hours = minutes / 60
    days = hours / 24
    weeks = days / 7
    months = days / 30
    years = days / 365

    if seconds < 60:
        return "just now"
    elif minutes < 60:
        return f"{int(minutes)} minute{'s' if int(minutes) != 1 else ''} ago"
    elif hours < 24:
        return f"{int(hours)} hour{'s' if int(hours) != 1 else ''} ago"
    elif days < 7:
        return f"{int(days)} day{'s' if int(days) != 1 else ''} ago"
    elif weeks < 4:
        return f"{int(weeks)} week{'s' if int(weeks) != 1 else ''} ago"
    elif months < 12:
        return f"{int(months)} month{'s' if int(months) != 1 else ''} ago"
    else:
        return f"{int(years)} year{'s' if int(years) != 1 else ''} ago"


def parse_natural_language_schedule(text: str) -> str | None:
    """
    Parse natural language schedule text into cron expression.

    Supports patterns like:
    - "every day at 3am" -> "0 3 * * *"
    - "every monday at 9am" -> "0 9 * * 1"
    - "every 15 minutes" -> "*/15 * * * *"
    - "every hour" -> "0 * * * *"
    - "every sunday at midnight" -> "0 0 * * 0"

    Args:
        text: Natural language schedule description.

    Returns:
        str | None: Cron expression or None if parsing fails.
    """
    text = text.lower().strip()

    # Map day names to cron day numbers
    day_map = {
        "sunday": "0",
        "monday": "1",
        "tuesday": "2",
        "wednesday": "3",
        "thursday": "4",
        "friday": "5",
        "saturday": "6",
    }

    # Parse time
    time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text)
    hour = 0
    minute = 0

    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        am_pm = time_match.group(3)

        if am_pm == "pm" and hour != 12:
            hour += 12
        elif am_pm == "am" and hour == 12:
            hour = 0

    # Check for "midnight"
    if "midnight" in text:
        hour = 0
        minute = 0

    # Parse frequency
    if "every minute" in text:
        return "* * * * *"
    elif re.search(r"every \d+ minutes", text):
        match = re.search(r"every (\d+) minutes", text)
        if match:
            return f"*/{match.group(1)} * * * *"
    elif "every hour" in text:
        return "0 * * * *"
    elif "every day" in text:
        return f"{minute} {hour} * * *"
    elif "every week" in text or "every month" in text:
        return f"{minute} {hour} * * *"
    elif "every year" in text:
        return f"{minute} {hour} 1 1 *"

    # Parse day of week
    for day_name, day_num in day_map.items():
        if day_name in text:
            return f"{minute} {hour} * * {day_num}"

    logger.warning(f"Failed to parse natural language schedule: {text}")
    return None


def get_cron_human_readable(cron_expr: str) -> str | None:
    """
    Convert a cron expression to human-readable format.

    Args:
        cron_expr: Cron expression (5 fields: minute hour day month weekday).

    Returns:
        str | None: Human-readable description or None if invalid.
    """
    try:
        parts = cron_expr.split()
        if len(parts) != 5:
            return None

        minute, hour, day, month, weekday = parts

        # Parse minute
        if minute == "*":
            minute_str = "every minute"
        elif minute.startswith("*/"):
            minute_str = f"every {minute[2:]} minutes"
        else:
            minute_str = f"at minute {minute}"

        # Parse hour
        if hour == "*":
            hour_str = "of every hour"
        elif hour.startswith("*/"):
            hour_str = f"every {hour[2:]} hours"
        else:
            hour_int = int(hour)
            am_pm = "AM" if hour_int < 12 else "PM"
            display_hour = hour_int if hour_int <= 12 else hour_int - 12
            if display_hour == 0:
                display_hour = 12
            hour_str = f"at {display_hour}:00 {am_pm}"

        # Parse day
        if day == "*":
            day_str = "of every month"
        elif day.startswith("*/"):
            day_str = f"every {day[2:]} days"
        else:
            day_str = f"on day {day}"

        # Parse month
        if month == "*":
            month_str = ""
        elif month.startswith("*/"):
            month_str = f" every {month[2:]} months"
        else:
            month_str = f" in month {month}"

        # Parse weekday
        weekday_map = {
            "0": "Sunday",
            "1": "Monday",
            "2": "Tuesday",
            "3": "Wednesday",
            "4": "Thursday",
            "5": "Friday",
            "6": "Saturday",
            "*": "",
        }
        weekday_str = ""
        if weekday != "*":
            weekday_str = f" on {weekday_map.get(weekday, weekday)}"

        # Combine
        if minute == "*" and hour == "*" and day == "*" and month == "*" and weekday == "*":
            return "every minute"
        elif minute != "*" and hour == "*" and day == "*" and month == "*" and weekday == "*":
            return minute_str
        elif hour != "*" and day == "*" and month == "*" and weekday == "*":
            return f"{minute_str} {hour_str}"
        else:
            return f"{minute_str} {hour_str} {day_str}{month_str}{weekday_str}"

    except Exception as e:
        logger.warning(f"Failed to parse cron expression '{cron_expr}': {e}")
        return None


def calculate_age_days(dt: datetime) -> int:
    """
    Calculate the age of a datetime in days.

    Args:
        dt: Datetime to calculate age from.

    Returns:
        int: Age in days.
    """
    diff = datetime.now() - dt
    return diff.days


def is_within_days(dt: datetime, days: int) -> bool:
    """
    Check if a datetime is within the last N days.

    Args:
        dt: Datetime to check.
        days: Number of days.

    Returns:
        bool: True if within the last N days.
    """
    return calculate_age_days(dt) <= days


def truncate_to_date(dt: datetime) -> datetime:
    """
    Truncate datetime to date (midnight).

    Args:
        dt: Datetime to truncate.

    Returns:
        datetime: Datetime at midnight of the same day.
    """
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def get_date_range(
    start: datetime | None = None,
    end: datetime | None = None,
    days: int | None = None,
) -> tuple[datetime, datetime]:
    """
    Get a date range.

    Args:
        start: Start date (defaults to now - days if days provided).
        end: End date (defaults to now).
        days: Number of days for range.

    Returns:
        tuple[datetime, datetime]: (start_date, end_date)
    """
    if end is None:
        end = datetime.now()

    if start is None:
        if days:
            start = end - timedelta(days=days)
        else:
            start = datetime.now()

    return (truncate_to_date(start), truncate_to_date(end))


def datetime_to_iso(dt: datetime) -> str:
    """
    Convert datetime to ISO 8601 format.

    Args:
        dt: Datetime to convert.

    Returns:
        str: ISO 8601 formatted string.
    """
    return dt.isoformat()


def iso_to_datetime(iso_str: str) -> datetime | None:
    """
    Convert ISO 8601 string to datetime.

    Args:
        iso_str: ISO 8601 formatted string.

    Returns:
        datetime | None: Parsed datetime or None if parsing fails.
    """
    try:
        # Handle both with and without timezone
        if iso_str.endswith("Z"):
            iso_str = iso_str[:-1] + "+00:00"

        return datetime.fromisoformat(iso_str)
    except ValueError:
        logger.warning(f"Failed to parse ISO datetime: {iso_str}")
        return None


def get_timestamp() -> int:
    """
    Get current Unix timestamp.

    Returns:
        int: Current Unix timestamp.
    """
    return int(datetime.now().timestamp())


def timestamp_to_datetime(timestamp: int | float) -> datetime:
    """
    Convert Unix timestamp to datetime.

    Args:
        timestamp: Unix timestamp.

    Returns:
        datetime: Datetime object.
    """
    return datetime.fromtimestamp(timestamp)
