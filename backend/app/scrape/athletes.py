from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from app.calendar_2026 import SEASON
from app.scrape.http import Fetcher

ATHLETE_URL = "https://www.ironman.com/proseries/triathletes/{slug}"

_YEAR_RE = re.compile(r"\b(20\d{2})\b")
_RACE_HREF_RE = re.compile(r"/proseries/races/([a-z0-9-]+)")


@dataclass
class AthleteResultRow:
    event_title: str
    points: int | None
    distance: str
    race_slug: str | None = None
    year: int | None = None


def _int_or_none(text: str | None) -> int | None:
    if text is None:
        return None
    cleaned = text.strip()
    if cleaned in {"", "—", "-", "–"}:
        return None
    digits = re.sub(r"[^0-9]", "", cleaned)
    return int(digits) if digits else None


def parse_athlete_page(
    html: str, season: int = SEASON
) -> list[AthleteResultRow]:
    """Parse the athlete's IRONMAN Event History table.

    The table interleaves every season with no per-season container, so each
    row is filtered by the year in its date cell (``views-field-createdon``).
    """
    soup = BeautifulSoup(html, "lxml")
    rows: list[AthleteResultRow] = []
    for tr in soup.select("tr"):
        points_cell = tr.select_one("td.views-field-wtc-points")
        if points_cell is None:
            continue
        title_el = (
            tr.select_one("td.views-field-title-1 .event-title")
            or tr.select_one("td.views-field-title-1")
            or tr.select_one(".event-title")
        )
        if title_el is None:
            continue
        title = title_el.get_text(" ", strip=True)
        if not title:
            continue

        date_cell = tr.select_one("td.views-field-createdon")
        m = _YEAR_RE.search(date_cell.get_text()) if date_cell else None
        year = int(m.group(1)) if m else None
        if season is not None and year != season:
            continue

        link = tr.select_one('a[href*="/proseries/races/"]')
        race_slug = None
        if link:
            hm = _RACE_HREF_RE.search(link.get("href") or "")
            race_slug = hm.group(1) if hm else None

        logo = tr.select_one("div.race-type-logo")
        logo_classes = " ".join(logo.get("class") or []) if logo else ""
        if "70.3" in logo_classes:
            distance = "im703"
        elif logo_classes:
            distance = "im"
        else:  # some rows (e.g. DNF) carry no logo — fall back to the title
            distance = "im703" if "70.3" in title else "im"

        rows.append(
            AthleteResultRow(
                event_title=title,
                points=_int_or_none(points_cell.get_text()),
                distance=distance,
                race_slug=race_slug,
                year=year,
            )
        )
    return rows


def fetch_athlete(
    fetcher: Fetcher, slug: str, season: int = SEASON
) -> list[AthleteResultRow]:
    html = fetcher.get(ATHLETE_URL.format(slug=slug))
    return parse_athlete_page(html, season=season)
