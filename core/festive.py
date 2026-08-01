"""Automatic festival dressing.

The shop dresses itself for the big days with nobody switching anything on.
A context processor asks this module what today is; the answer becomes a
`data-festival` attribute on <html>, and festive.css does the rest — accent
hues, the ambient light, the announcement line. Match nothing and the site
looks exactly as it always does.

Fixed-date festivals are computed from the calendar. Lunar ones move every
year, so they live in LUNAR_DATES below and have to be topped up — one line
per festival per year. test_festive.py fails once the table runs out, which
is the reminder to extend it.

Manual control, for when the automatic answer is not the wanted one:
    ?theme=diwali   preview/force a theme for this browser (session)
    ?theme=auto     back to the calendar
    ?theme=off      plain shop, no festival
    FESTIVE_THEME   env var — forces one theme for everyone, ignores the date
"""
from __future__ import annotations

import datetime as dt
import os

SESSION_KEY = "festive_theme"

# ---------------------------------------------------------------------------
# What each festival looks like and says.
# `note` is the announcement line; keep it short, it sits in the top bar.
# ---------------------------------------------------------------------------
FESTIVALS = {
    "newyear":   {"label": "New Year",         "note": "New Year Edit · begin it in gold"},
    "valentine": {"label": "Valentine's Day",  "note": "The Valentine Edit · say it in gold"},
    "holi":      {"label": "Holi",             "note": "Holi Edit · colour that never fades"},
    "eid":       {"label": "Eid",              "note": "Eid Mubarak · the Eid Edit is here"},
    "akshaya":   {"label": "Akshaya Tritiya",  "note": "Akshaya Tritiya · the day for gold"},
    "rakhi":     {"label": "Raksha Bandhan",   "note": "Rakhi Edit · something for your sister"},
    "diwali":    {"label": "Diwali",           "note": "The Diwali Edit · gifting, wrapped and ready"},
    "christmas": {"label": "Christmas",        "note": "The Christmas Edit · under the tree by the 24th"},
}

# Festivals that sit on the same Gregorian date every year.
#   slug: ((month, day), days_before, days_after)
FIXED_DATES = {
    "christmas": ((12, 25), 12, 1),
    "newyear":   ((1, 1),    3, 2),
    "valentine": ((2, 14),   8, 1),
}

# Lunar festivals — the main day, per year.
#   ⚠ These are best-effort dates. Verify each year against a panchang before
#   the season and correct the line; a wrong date here only means the shop
#   dresses up on the wrong day, nothing breaks.
LUNAR_DATES = {
    2026: {"holi": (3, 4), "eid": (3, 20), "akshaya": (4, 19), "rakhi": (8, 28), "diwali": (11, 8)},
    2027: {"holi": (3, 22), "eid": (3, 9), "akshaya": (5, 8), "rakhi": (8, 17), "diwali": (10, 29)},
    2028: {"holi": (3, 11), "eid": (2, 26), "akshaya": (4, 27), "rakhi": (8, 5), "diwali": (10, 17)},
}

# How long the shop stays dressed, per lunar festival: (days_before, days_after)
LUNAR_WINDOWS = {
    "holi":    (3, 1),
    "eid":     (7, 1),
    "akshaya": (5, 1),
    "rakhi":   (7, 1),
    "diwali":  (12, 2),   # opens around Dhanteras, closes after Bhai Dooj
}


def _windows_for_year(year: int) -> list[tuple[str, dt.date, dt.date, dt.date]]:
    """Every (slug, start, main_day, end) window that touches `year`."""
    out = []

    for slug, ((month, day), before, after) in FIXED_DATES.items():
        try:
            main = dt.date(year, month, day)
        except ValueError:                      # Feb 29 and friends
            continue
        out.append((slug, main - dt.timedelta(days=before), main, main + dt.timedelta(days=after)))

    for slug, (month, day) in LUNAR_DATES.get(year, {}).items():
        before, after = LUNAR_WINDOWS.get(slug, (5, 1))
        main = dt.date(year, month, day)
        out.append((slug, main - dt.timedelta(days=before), main, main + dt.timedelta(days=after)))

    return out


def theme_for_date(today: dt.date) -> str | None:
    """The festival slug for a date, or None. Nearest main day wins overlaps."""
    # Neighbouring years are included because the New Year window straddles
    # 31 December: on 30 Dec the live window belongs to *next* year's 1 Jan,
    # and on 2 Jan it belongs to this year's.
    candidates = (
        _windows_for_year(today.year - 1)
        + _windows_for_year(today.year)
        + _windows_for_year(today.year + 1)
    )
    live = [(abs((main - today).days), slug) for slug, start, main, end in candidates
            if start <= today <= end]
    return min(live)[1] if live else None


def theme_payload(slug: str | None) -> dict | None:
    """What the templates get: slug, label, announcement line."""
    if not slug or slug not in FESTIVALS:
        return None
    return {"slug": slug, **FESTIVALS[slug]}


def resolve(request=None, today: dt.date | None = None) -> dict | None:
    """The active theme for this request — env override, then session, then date."""
    forced = os.getenv("FESTIVE_THEME", "").strip().lower()
    if forced:
        return None if forced in {"off", "none"} else theme_payload(forced)

    if request is not None:
        wanted = (request.GET.get("theme") or "").strip().lower()
        session = getattr(request, "session", None)

        if wanted and session is not None:
            if wanted == "auto":
                session.pop(SESSION_KEY, None)
            else:
                session[SESSION_KEY] = wanted       # "off" is a valid choice

        chosen = (session or {}).get(SESSION_KEY) if session is not None else None
        if chosen == "off":
            return None
        if chosen:
            return theme_payload(chosen)

    return theme_payload(theme_for_date(today or dt.date.today()))
