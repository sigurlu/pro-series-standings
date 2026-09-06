"""Pure scoring logic for the Pro Series ceiling standings. No IO."""

from __future__ import annotations

import itertools
from dataclasses import dataclass


@dataclass(frozen=True)
class ScoredRace:
    id: int
    points: int
    is_full_im: bool


def is_full_im(distance: str, is_world_championship: bool) -> bool:
    """A full IRONMAN counts against the max-3 cap. IM WC included; 70.3 WC not."""
    return distance == "im"


def is_eligible(athlete_gender: str, eligible_gender: str) -> bool:
    """Whether an athlete of the given gender may start a race with this
    eligible_gender marker (``W``, ``M`` or ``both``)."""
    return eligible_gender in (athlete_gender, "both")


def best_legal_total(results: list[ScoredRace]) -> tuple[int, list[ScoredRace]]:
    """Best sum over subsets of size 0..min(5, n) with at most 3 full IRONMAN."""
    n = len(results)
    best_total = 0
    best_subset: list[ScoredRace] = []
    for size in range(0, min(5, n) + 1):
        for subset in itertools.combinations(results, size):
            if sum(1 for r in subset if r.is_full_im) > 3:
                continue
            total = sum(r.points for r in subset)
            if total > best_total:
                best_total = total
                best_subset = list(subset)
    return best_total, best_subset


def ceiling_total(completed: list[ScoredRace], remaining: list[ScoredRace]) -> int:
    """Theoretical max: best legal total over completed results plus every
    remaining eligible race scored at its max points."""
    return best_legal_total(completed + remaining)[0]
