from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from app.scrape.http import Fetcher

_BIB_RE = re.compile(r"^\s*([FMfm])\s?\d+\s*$")


@dataclass
class StartListRow:
    gender: str  # "W" (bib F) or "M" (bib M)
    name: str
    country: str | None


def parse_start_list(html: str) -> list[StartListRow]:
    """Parse the pro start-list table(s). Rows look like
    ``[bib, first, last, country]`` with the bib prefixed ``F`` or ``M``; the
    name may span several cells, the country is always the last cell."""
    soup = BeautifulSoup(html, "lxml")
    out: list[StartListRow] = []
    seen: set[tuple[str, str]] = set()
    for table in soup.select("table"):
        for tr in table.select("tr"):
            cells = [
                td.get_text(" ", strip=True).replace("\xa0", " ")
                for td in tr.find_all(["td", "th"])
            ]
            if len(cells) < 3:
                continue
            m = _BIB_RE.match(cells[0])
            if not m:
                continue
            gender = "W" if m.group(1).upper() == "F" else "M"
            name = " ".join(c for c in cells[1:-1] if c).strip()
            country = cells[-1].strip() or None
            if not name:
                continue
            key = (gender, name.casefold())
            if key in seen:
                continue
            seen.add(key)
            out.append(StartListRow(gender=gender, name=name, country=country))
    return out


def fetch_start_list(fetcher: Fetcher, url: str) -> list[StartListRow]:
    return parse_start_list(fetcher.get(url))
