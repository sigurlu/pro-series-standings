from datetime import date

from app.calendar_2026 import RACES
from app.models import Athlete, Race
from app.scoring import (
    ScoredRace,
    best_legal_total,
    ceiling_total,
    is_eligible,
)
from app.scrape.persist import _remaining_for, athlete_ceiling


def _rid(race: Race, i: int) -> Race:
    race.id = i
    return race


def _im(id_: int, points: int) -> ScoredRace:
    return ScoredRace(id=id_, points=points, is_full_im=True)


def _half(id_: int, points: int) -> ScoredRace:
    return ScoredRace(id=id_, points=points, is_full_im=False)


def test_ceiling_drops_weakest_not_a_fourth_im():
    completed = [_im(1, 5000), _im(2, 5000), _im(3, 5000), _half(4, 2500), _half(5, 2400)]
    remaining = [ScoredRace(id=6, points=6000, is_full_im=True)]
    assert ceiling_total(completed, remaining) == 20900


def test_ceiling_respects_max_three_full_im():
    # Four completed results, only two of them full IRONMAN.
    completed = [_im(1, 4800), _im(2, 4700), _half(3, 2500), _half(4, 2400)]
    remaining = [
        ScoredRace(id=5, points=3000, is_full_im=False),  # 70.3 WC
        ScoredRace(id=6, points=6000, is_full_im=True),  # IM WC
    ]
    total, chosen = best_legal_total(completed + remaining)
    assert sum(1 for r in chosen if r.is_full_im) <= 3
    # best legal five: 6000 + 4800 + 4700 (3 IM) + 3000 + 2500 (2x 70.3) = 21000
    assert total == 21000
    assert ceiling_total(completed, remaining) == 21000


def test_no_remaining_ceiling_equals_current():
    completed = [_im(1, 5000), _half(2, 2500), _half(3, 2000)]
    assert ceiling_total(completed, []) == best_legal_total(completed)[0]


def test_gender_filter_excludes_women_only_race_for_male_athlete():
    remaining_for_male = [r for r in RACES if is_eligible("M", r["eligible_gender"])]
    slugs = {r["slug"] for r in remaining_for_male}
    assert "im-hamburg" not in slugs  # women only
    assert "im-frankfurt" in slugs  # men only
    assert "im-texas" in slugs  # both


def _race(slug: str, gender: str, distance: str, status: str) -> Race:
    return Race(
        season=2026,
        slug=slug,
        title=slug.replace("-", " "),
        date=date(2026, 6, 7),
        distance=distance,
        is_world_championship=False,
        max_points=5000 if distance == "im" else 2500,
        eligible_gender=gender,
        status=status,
    )


def test_persist_remaining_filter_and_ceiling_for_male_athlete():
    """Integration of the persist gender filter with scoring: a women-only race
    (Hamburg) must never enter a male athlete's remaining set or ceiling."""
    male = Athlete(ironman_nid=1, slug="john-smith", name="John Smith", gender="M")
    races = [
        _race("im-hamburg", "W", "im", "upcoming"),
        _race("im-frankfurt", "M", "im", "upcoming"),
        _race("im-texas", "both", "im", "upcoming"),
        _race("im703-swansea", "both", "im703", "completed"),
    ]

    remaining = _remaining_for(male, races)
    slugs = {r.slug for r in remaining}
    assert "im-hamburg" not in slugs  # women only
    assert "im-frankfurt" in slugs  # men only
    assert "im-texas" in slugs  # both
    assert "im703-swansea" not in slugs  # already completed

    completed = [_half(1, 2000)]
    remaining_scored = [
        ScoredRace(id=r.id or i, points=r.max_points, is_full_im=r.distance == "im")
        for i, r in enumerate(remaining, start=100)
    ]
    ceiling = ceiling_total(completed, remaining_scored)
    # Frankfurt 5000 + Texas 5000 (2 IM) + Hamburg excluded, + completed 2000
    assert ceiling == 12000


def test_remaining_gated_by_start_list():
    """Once a start list exists for a race, only listed athletes keep it."""
    alice = Athlete(ironman_nid=1, slug="alice", name="Alice", gender="W")
    alice.id = 1
    bob = Athlete(ironman_nid=2, slug="bob", name="Bob", gender="W")
    bob.id = 2
    wc = _rid(_race("im-world-championship", "both", "im", "upcoming"), 10)
    kalmar = _rid(_race("im-kalmar", "both", "im", "upcoming"), 11)  # not gated

    gated = {10}
    pairs = {(10, alice.id)}  # only Alice is on the WC start list

    alice_slugs = {r.slug for r in _remaining_for(alice, [wc, kalmar], gated, pairs)}
    bob_slugs = {r.slug for r in _remaining_for(bob, [wc, kalmar], gated, pairs)}

    assert alice_slugs == {"im-world-championship", "im-kalmar"}
    assert bob_slugs == {"im-kalmar"}  # WC dropped — Bob isn't racing it


def test_athlete_ceiling_complete_data_matches_ceiling_total():
    completed = [_im(1, 5000), _im(2, 4800), _half(3, 2500), _half(4, 2400)]
    remaining = [ScoredRace(id=9, points=6000, is_full_im=True)]
    # official == computed: nothing unseen, so it's just the plain calc
    computed = best_legal_total(completed)[0]
    assert athlete_ceiling(completed, remaining, computed, computed) == (
        ceiling_total(completed, remaining)
    )


def test_athlete_ceiling_does_not_stack_unseen_points_on_a_full_slate():
    # We can only see 3 of her results; the standing says she has 14663.
    completed = [_im(1, 5000), _im(2, 4922), _half(3, 2241)]
    computed = best_legal_total(completed)[0]  # 12163
    official = 14663
    remaining = [
        ScoredRace(id=8, points=3000, is_full_im=False),  # 70.3 Worlds
        ScoredRace(id=9, points=6000, is_full_im=True),  # Kona
    ]
    ceiling = athlete_ceiling(completed, remaining, official, computed)

    # the old bug added the full 9000 on top of the official total
    assert ceiling < official + 9000
    # remaining races displace her weak (partly unseen) results instead
    assert ceiling == 21163
    assert ceiling >= official  # headroom never negative


def test_athlete_ceiling_no_remaining_equals_official():
    completed = [_im(1, 5000), _half(2, 2000)]
    assert athlete_ceiling(completed, [], 9000, best_legal_total(completed)[0]) == 9000
