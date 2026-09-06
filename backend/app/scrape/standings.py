from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from app.scrape.http import Fetcher

STANDINGS_URL = "https://www.ironman.com/proseries/standings/2026"

_RACE_HREF_RE = re.compile(r"/proseries/races/([a-z0-9-]+)")


@dataclass
class AthleteRow:
    nid: int
    slug: str
    name: str
    country_code: str | None
    rank: int
    official_points: int
    rank_diff: int


@dataclass
class RaceResultRow:
    """A row of the standings page's race table. Used only as a calendar
    cross-check — completion is derived from athlete results, not from here."""

    slug: str | None
    title: str
    max_points: int | None


@dataclass
class StandingsPage:
    W: list[AthleteRow] = field(default_factory=list)
    M: list[AthleteRow] = field(default_factory=list)
    race_results: list[RaceResultRow] = field(default_factory=list)


def _int_or_none(text: str | None) -> int | None:
    if text is None:
        return None
    digits = re.sub(r"[^0-9]", "", text)
    return int(digits) if digits else None


def _country_from_flag(cell) -> str | None:
    holder = cell.select_one(".country-flag-formatter img")
    if holder is None:
        return None
    src = holder.get("src") or ""
    m = re.search(r"/([a-zA-Z]{2})\.(?:svg|png|gif|jpg)", src)
    if m:
        return m.group(1).upper()
    return None


def _rank_diff(row) -> int:
    up = row.select_one(".rank-change--up .number")
    if up is not None:
        return _int_or_none(up.get_text()) or 0
    down = row.select_one(".rank-change--down .number")
    if down is not None:
        return -(_int_or_none(down.get_text()) or 0)
    return 0


def _parse_gender_table(container) -> list[AthleteRow]:
    rows: list[AthleteRow] = []
    if container is None:
        return rows
    for tr in container.select("table tbody tr"):
        classes = tr.get("class") or []
        if "points-breakdown" in classes:
            continue
        toggle = tr.select_one("a.toggle-points")
        if toggle is None or not toggle.get("data-athlete-nid"):
            continue
        nid = int(toggle["data-athlete-nid"])
        profile = tr.select_one('a[href*="/proseries/triathletes/"]')
        if profile is None:
            continue
        slug = profile["href"].rstrip("/").split("/")[-1]
        name = profile.get_text(strip=True)
        cells = tr.find_all("td")
        rank = 0
        for td in cells:
            val = _int_or_none(td.get_text())
            if val is not None and td.get_text(strip=True).isdigit():
                rank = val
                break
        points_cell = tr.select_one("td.views-field-points")
        official_points = _int_or_none(points_cell.get_text()) if points_cell else 0
        country = None
        for td in cells:
            country = _country_from_flag(td)
            if country:
                break
        rows.append(
            AthleteRow(
                nid=nid,
                slug=slug,
                name=name,
                country_code=country,
                rank=rank,
                official_points=official_points or 0,
                rank_diff=_rank_diff(tr),
            )
        )
    return rows


def _parse_race_results(soup) -> list[RaceResultRow]:
    """Read the standings page's cols-7 race table. Each title cell links to
    ``/proseries/races/<slug>`` — the slug matches our seed calendar."""
    table = soup.select_one("table.cols-7")
    if table is None:
        for candidate in soup.select("table"):
            if candidate.select_one('a[href*="/proseries/races/"]'):
                table = candidate
                break
    if table is None:
        return []
    out: list[RaceResultRow] = []
    for tr in table.select("tbody tr"):
        title_cell = tr.select_one("td.views-field-title, td.views-field-title-1")
        if title_cell is None:
            continue
        title = title_cell.get_text(" ", strip=True)
        if not title:
            continue
        link = title_cell.select_one('a[href*="/proseries/races/"]')
        slug = None
        if link:
            m = _RACE_HREF_RE.search(link.get("href") or "")
            slug = m.group(1) if m else None
        points_cell = tr.select_one(
            "td.views-field-field-points, td.views-field-points"
        )
        out.append(
            RaceResultRow(
                slug=slug,
                title=title,
                max_points=_int_or_none(points_cell.get_text())
                if points_cell
                else None,
            )
        )
    return out


def parse_standings_page(html: str) -> StandingsPage:
    soup = BeautifulSoup(html, "lxml")
    return StandingsPage(
        W=_parse_gender_table(soup.select_one(".standings-search--female")),
        M=_parse_gender_table(soup.select_one(".standings-search--male")),
        race_results=_parse_race_results(soup),
    )


def parse_all(fetcher: Fetcher) -> StandingsPage:
    """Walk the standings pager. The pager is 0-indexed: ``?page=0`` (same as
    no param) is ranks 1-10, ``?page=1`` is 11-20, and so on."""
    combined = StandingsPage()
    seen_w: set[int] = set()
    seen_m: set[int] = set()
    page = 0
    while True:
        url = f"{STANDINGS_URL}?page={page}"
        html = fetcher.get(url)
        parsed = parse_standings_page(html)
        if page == 0:
            combined.race_results = parsed.race_results

        new_w = [r for r in parsed.W if r.nid not in seen_w]
        new_m = [r for r in parsed.M if r.nid not in seen_m]
        for r in new_w:
            seen_w.add(r.nid)
        for r in new_m:
            seen_m.add(r.nid)
        combined.W.extend(new_w)
        combined.M.extend(new_m)

        w_done = len(new_w) == 0 or len(parsed.W) < 10
        m_done = len(new_m) == 0 or len(parsed.M) < 10
        if w_done and m_done:
            break
        page += 1
        if page > 60:
            break
    return combined
