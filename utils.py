from datetime import datetime, timedelta, date

def parse_relative_date(time_str: str):
    """Parse a time string (relative like '3 hours ago', 'Yesterday', or absolute date) into a date object.
    Returns a datetime.date object or None if unrecognized."""
    if not time_str:
        return None
    text = time_str.lower()
    today = date.today()
    if "hour ago" in text or "hours ago" in text or "minutes ago" in text or "min ago" in text:
        # Anything referring to today (hours/minutes ago -> treat as today)
        return today
    if "yesterday" in text:
        return today - timedelta(days=1)
    # Absolute date format examples (MarketWatch might have):
    # e.g. "Jan 5, 2025", or "Jan 5, 2025 10:00 a.m. ET" -> we parse just the date part
    try:
        # Try common date formats
        # Remove trailing time or timezone if present
        comma_parts = time_str.split(',')
        if len(comma_parts) >= 2:
            # Likely format like "Jan 5, 2025 ..."
            date_part = comma_parts[0] + ',' + comma_parts[1]
        else:
            date_part = time_str
        # Try parsing
        parsed = datetime.strptime(date_part.strip(), "%b %d, %Y")
        return parsed.date()
    except Exception:
        try:
            # Try without year (maybe the string was "Jan 5" without year)
            parsed = datetime.strptime(time_str.strip(), "%b %d")
            # If parsed without year, assign current year
            return parsed.replace(year=today.year).date()
        except Exception:
            return None
