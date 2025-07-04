from datetime import datetime, timedelta, date
import re

def parse_relative_date(time_str: str):

    if not time_str:
        return None

    txt = time_str.strip().lower()
    today = date.today()



    # ---------- ISO 8601 (YYYY-MM-DD) ----------
    iso_match = re.match(r"\d{4}-\d{2}-\d{2}", txt)
    if iso_match:
        try:
            return datetime.strptime(iso_match.group(), "%Y-%m-%d").date()
        except ValueError:
            pass





    # ---------- relative phrases ----------
    if any(word in txt for word in ("hour", "hours", "minute", "minutes", "just now")):
        return today
    if "yesterday" in txt:
        return today - timedelta(days=1)
    if "day ago" in txt or "days ago" in txt:
        try:
            n = int(txt.split()[0])
            return today - timedelta(days=n)
        except Exception:
            pass




    # ---------- absolute long / short month ----------
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(time_str, fmt).date()
        except ValueError:
            continue





    # ---------- fallback: 'Jan 5' => assume current year ----------
    try:
        d = datetime.strptime(time_str, "%b %d")
        return d.replace(year=today.year).date()
    except Exception:
        return None
