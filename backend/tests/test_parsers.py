from datetime import date
from pathlib import Path

import pytest

from app.models import Athlete, Race
from app.scrape.athletes import parse_athlete_page
from app.scrape.persist import (
    AthleteNameIndex,
    _match_seed_race,
    _race_is_done,
    _slug_matches,
    fuzzy_match,
)
from app.scrape.standings import parse_standings_page
from app.scrape.startlists import parse_start_list

FIXTURES = Path(__file__).parent / "fixtures"


class _FakeScalars:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items

    def __iter__(self):
        return iter(self._items)


class _FakeDB:
    def __init__(self, races):
        self._races = races

    def scalars(self, *_args, **_kwargs):
        return _FakeScalars(self._races)


def test_parse_standings_page_woman_row():
    html = (FIXTURES / "standings_snippet.html").read_text()
    page = parse_standings_page(html)

    assert len(page.W) == 1
    row = page.W[0]
    assert row.nid == 12345
    assert row.slug == "jane-doe"
    assert row.name == "Jane Doe"
    assert row.official_points == 15000
    assert row.rank == 1
    assert row.rank_diff == 2
    assert row.country_code == "US"
    assert page.M == []


def test_parse_standings_page_race_results():
    html = (FIXTURES / "standings_snippet.html").read_text()
    page = parse_standings_page(html)

    assert len(page.race_results) == 1
    rr = page.race_results[0]
    assert rr.slug == "im-new-zealand"
    assert rr.max_points == 5000
    # title cell has a <br>; parser inserts a space so tokens stay separable
    assert fuzzy_match(rr.title, "ANZCO Foods IRONMAN New Zealand")


def test_parse_athlete_page_filters_to_season():
    html = (FIXTURES / "athlete_snippet.html").read_text()
    rows = parse_athlete_page(html, season=2026)

    # only the 2026 row survives; the 2025 Oceanside row is dropped
    assert len(rows) == 1
    r = rows[0]
    assert r.event_title == "IRONMAN 70.3 Geelong"
    assert r.points == 2500
    assert r.distance == "im703"
    assert r.race_slug == "im703-geelong"
    assert r.year == 2026


def test_parse_athlete_page_other_season():
    html = (FIXTURES / "athlete_snippet.html").read_text()
    rows = parse_athlete_page(html, season=2025)
    assert [r.race_slug for r in rows] == ["im703-oceanside"]


@pytest.mark.parametrize(
    "a,b",
    [
        ("Memorial Hermann IRONMAN Texas", "IRONMAN Texas"),
        ("IRONMAN Hamburg European Championship", "IRONMAN Hamburg"),
        ("IRONMAN Kalmar-Sweden", "IRONMAN Kalmar"),
        ("IRONMAN 70.3 Zell am See-Kaprun", "IRONMAN 70.3 Zell am See"),
        ("IRONMAN 70.3 Pennsylvania Happy Valley", "IRONMAN 70.3 Pennsylvania"),
        ("Athletic Brewing IRONMAN 70.3 Oceanside", "IRONMAN 70.3 Oceanside"),
    ],
)
def test_fuzzy_match_handles_sponsors_and_suffixes(a, b):
    assert fuzzy_match(a, b)


def test_fuzzy_match_rejects_different_venues():
    assert not fuzzy_match("IRONMAN Texas", "IRONMAN Kalmar")
    assert not fuzzy_match("IRONMAN 70.3 Geelong", "IRONMAN 70.3 Swansea")


def test_race_is_done_uses_date_then_scored_results():
    today = date(2026, 9, 5)
    past = Race(season=2026, slug="im703-zell-am-see", title="", date=date(2026, 8, 30),
               distance="im703", is_world_championship=False, max_points=2500,
               eligible_gender="both")
    past.id = 1
    future = Race(season=2026, slug="im-world-championship", title="", date=date(2026, 10, 10),
                  distance="im", is_world_championship=True, max_points=6000,
                  eligible_gender="both")
    future.id = 2

    # past race with no points published yet -> still done (not winnable)
    assert _race_is_done(past, today, scored_race_ids=set())
    # future race -> not done, even if it somehow has an early result
    assert not _race_is_done(future, today, scored_race_ids=set())
    assert _race_is_done(future, today, scored_race_ids={2})


def test_slug_matches_prefix():
    assert _slug_matches("im-world-championship", "im-world-championship-kona")
    assert _slug_matches("im703-world-championship-w", "im703-world-championship")
    assert not _slug_matches("im-texas", "im703-texas")


def _race(slug, title, distance, gender="both") -> Race:
    return Race(
        season=2026,
        slug=slug,
        title=title,
        date=date(2026, 6, 1),
        distance=distance,
        is_world_championship="world-championship" in slug,
        max_points=5000 if distance == "im" else 2500,
        eligible_gender=gender,
    )


def test_match_seed_race_by_href_slug():
    db = _FakeDB([_race("im-kalmar", "IRONMAN Kalmar", "im")])
    hit = _match_seed_race(
        db, slug="im-kalmar", title="IRONMAN Kalmar-Sweden", distance="im"
    )
    assert hit is not None and hit.slug == "im-kalmar"


def test_match_seed_race_kona_prefix():
    db = _FakeDB([_race("im-world-championship", "IRONMAN World Championship", "im")])
    hit = _match_seed_race(db, slug="im-world-championship-kona", distance="im")
    assert hit is not None and hit.slug == "im-world-championship"


def test_match_seed_race_by_title_when_no_slug():
    db = _FakeDB([_race("im-texas", "IRONMAN Texas", "im")])
    hit = _match_seed_race(
        db, title="Memorial Hermann IRONMAN Texas", distance="im"
    )
    assert hit is not None and hit.slug == "im-texas"


def test_match_seed_race_ignores_non_series_event():
    db = _FakeDB([_race("im703-geelong", "IRONMAN 70.3 Geelong", "im703")])
    assert (
        _match_seed_race(
            db, slug="im703-poznan", title="IRONMAN 70.3 Poznan", distance="im703"
        )
        is None
    )


def test_match_seed_race_disambiguates_703_worlds_by_gender():
    db = _FakeDB(
        [
            _race("im703-world-championship-w", "IRONMAN 70.3 World Championship", "im703", "W"),
            _race("im703-world-championship-m", "IRONMAN 70.3 World Championship", "im703", "M"),
        ]
    )
    men = _match_seed_race(
        db, slug="im703-world-championship", distance="im703", gender="M"
    )
    women = _match_seed_race(
        db, title="IRONMAN 70.3 World Championship", distance="im703", gender="W"
    )
    assert men.slug == "im703-world-championship-m"
    assert women.slug == "im703-world-championship-w"


def test_parse_start_list_splits_by_bib_gender():
    html = (FIXTURES / "startlist_snippet.html").read_text()
    rows = parse_start_list(html)

    women = [r.name for r in rows if r.gender == "W"]
    men = [r.name for r in rows if r.gender == "M"]
    assert women == ["Lucy Charles-Barclay", "Marjolaine Pierré", "Kat Matthews"]
    assert men == ["Marten Van Riel", "Matthew Hanson", "Damien Le Mesnager"]


def _ath(slug: str, name: str, gender: str, i: int) -> Athlete:
    a = Athlete(ironman_nid=i, slug=slug, name=name, gender=gender)
    a.id = i
    return a


def test_athlete_name_index_exact_nickname_and_gender():
    idx = AthleteNameIndex(
        [
            _ath("matt-hanson", "Matt Hanson", "M", 1),
            _ath("marjolaine-pierre", "Marjolaine Pierré", "W", 2),
            _ath("marten-van-riel", "Marten Van Riel", "M", 3),
            _ath("matt-hanson-w", "Matt Hanson", "W", 4),  # unrelated same name
        ]
    )
    # accent-insensitive exact
    assert idx.find("W", "Marjolaine Pierre").id == 2
    # multi-word surname
    assert idx.find("M", "Marten Van Riel").id == 3
    # nickname: start list "Matthew Hanson" -> "Matt Hanson", correct gender
    assert idx.find("M", "Matthew Hanson").id == 1
    # gender keeps them apart
    assert idx.find("W", "Matthew Hanson").id == 4
    # genuinely absent
    assert idx.find("M", "Jan Frodeno") is None
