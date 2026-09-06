from __future__ import annotations

import logging
import re
import unicodedata
from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.calendar_2026 import RACES, SEASON, START_LISTS
from app.models import Athlete, Race, Result, Standing, StartListEntry
from app.scoring import ScoredRace, best_legal_total, ceiling_total
from app.scrape.athletes import fetch_athlete
from app.scrape.http import Fetcher
from app.scrape.standings import parse_all
from app.scrape.startlists import fetch_start_list

log = logging.getLogger(__name__)

# Generic words that carry no venue information. Live titles add sponsor
# prefixes ("Memorial Hermann IRONMAN Texas") and suffixes ("IRONMAN Hamburg
# European Championship", "IRONMAN Kalmar-Sweden"), so a seed title's
# distinctive tokens are always a subset of the scraped title's tokens.
_GENERIC_TOKENS = {
    "ironman",
    "703",
    "im",
    "im703",
    "the",
    "european",
    "asia",
    "pacific",
    "asiapacific",
    "oceania",
    "championship",
    "presented",
    "by",
    "series",
    "pro",
}


def _title_tokens(s: str) -> frozenset[str]:
    s = s.casefold().replace("70.3", " ")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return frozenset(t for t in s.split() if t and t not in _GENERIC_TOKENS)


def norm_title(s: str) -> str:
    """Sorted, space-joined distinctive tokens. For logging / debugging."""
    return " ".join(sorted(_title_tokens(s)))


def fuzzy_match(a: str, b: str) -> bool:
    """True when one title's distinctive tokens are a subset of the other's."""
    ta, tb = _title_tokens(a), _title_tokens(b)
    if not ta or not tb:
        return False
    return ta <= tb or tb <= ta


def _slug_matches(seed_slug: str, other: str) -> bool:
    """Exact, or one is a hyphen-delimited prefix of the other. Handles the
    site's ``im-world-championship-kona`` vs seed ``im-world-championship``."""
    if seed_slug == other:
        return True
    return other.startswith(seed_slug + "-") or seed_slug.startswith(other + "-")


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9\s]", " ", s.casefold()).split())


class AthleteNameIndex:
    """Resolve a free-text 'First Last' from a start list to a scraped athlete,
    within one gender. Exact normalized match first, then same last name with a
    first-name that is a prefix of the other (Matt / Matthew, Sam / Samuel)."""

    def __init__(self, athletes: list[Athlete]) -> None:
        self._exact: dict[tuple[str, str], Athlete] = {}
        self._by_last: dict[tuple[str, str], list[Athlete]] = {}
        for a in athletes:
            for text in (a.name, a.slug.replace("-", " ")):
                toks = norm_name(text).split()
                if not toks:
                    continue
                self._exact.setdefault((a.gender, " ".join(toks)), a)
                self._by_last.setdefault((a.gender, toks[-1]), []).append(a)

    def find(self, gender: str, name: str) -> Athlete | None:
        toks = norm_name(name).split()
        if not toks:
            return None
        hit = self._exact.get((gender, " ".join(toks)))
        if hit is not None:
            return hit
        if len(toks) < 2:
            return None
        first, last = toks[0], toks[-1]
        for a in self._by_last.get((gender, last), []):
            at = norm_name(a.name).split()
            if len(at) < 2:
                continue
            af = at[0]
            if min(len(af), len(first)) >= 3 and (
                af.startswith(first) or first.startswith(af)
            ):
                return a
        return None


def upsert_calendar(db: Session) -> int:
    existing = {r.slug: r for r in db.scalars(select(Race).where(Race.season == SEASON))}
    for row in RACES:
        race = existing.get(row["slug"])
        if race is None:
            race = Race(season=SEASON, slug=row["slug"])
            db.add(race)
        race.title = row["title"]
        race.date = date.fromisoformat(row["date"])
        race.distance = row["distance"]
        race.is_world_championship = row["is_world_championship"]
        race.max_points = row["max_points"]
        race.eligible_gender = row["eligible_gender"]
        # status is derived from athlete results after the scrape
        # (see _mark_completed); new rows default to "upcoming".
    db.flush()
    return len(RACES)


def _upsert_athlete(db: Session, row, gender: str, by_nid: dict[int, Athlete]) -> Athlete:
    athlete = by_nid.get(row.nid)
    if athlete is None:
        athlete = db.scalar(select(Athlete).where(Athlete.ironman_nid == row.nid))
    if athlete is None:
        athlete = Athlete(ironman_nid=row.nid, slug=row.slug, name=row.name)
        db.add(athlete)
    athlete.slug = row.slug
    athlete.name = row.name
    athlete.gender = gender
    if row.country_code:
        athlete.country_code = row.country_code
    by_nid[row.nid] = athlete
    db.flush()
    return athlete


def _upsert_standing(db: Session, athlete: Athlete, official_points: int, rank_diff: int) -> None:
    standing = db.scalar(
        select(Standing).where(
            Standing.athlete_id == athlete.id, Standing.season == SEASON
        )
    )
    if standing is None:
        standing = Standing(athlete_id=athlete.id, season=SEASON)
        db.add(standing)
    standing.official_points = official_points
    standing.rank_diff = rank_diff
    db.flush()


def _match_seed_race(
    db: Session,
    *,
    slug: str | None = None,
    title: str | None = None,
    distance: str | None = None,
    gender: str | None = None,
) -> Race | None:
    """Resolve a scraped event to a seed race. Prefers the ``/proseries/races/``
    URL slug (exact match on the site); falls back to fuzzy title tokens."""
    races = db.scalars(select(Race).where(Race.season == SEASON)).all()

    def _pick(cands: list[Race]) -> Race | None:
        if len(cands) > 1 and gender is not None:
            # the two 70.3 World Championship seed rows share slug + title
            gendered = [r for r in cands if r.eligible_gender == gender]
            if gendered:
                return gendered[0]
            both = [r for r in cands if r.eligible_gender == "both"]
            if both:
                return both[0]
        return cands[0] if cands else None

    if slug:
        hit = _pick(
            [
                r
                for r in races
                if _slug_matches(r.slug, slug)
                and (distance is None or r.distance == distance)
            ]
        )
        if hit is not None:
            return hit

    if title:
        return _pick(
            [
                r
                for r in races
                if (distance is None or r.distance == distance)
                and (
                    fuzzy_match(title, r.title)
                    or fuzzy_match(title, r.slug.replace("-", " "))
                )
            ]
        )

    return None


def run_scrape(db: Session, pages_only: bool = False) -> tuple[int, int]:
    """Scrape standings + athlete pages into the DB.

    Commits incrementally: once after the standings pass, then once per athlete
    page, then after deriving race completion and the final recompute. Progress
    is visible in the DB as it runs, and a mid-run failure keeps what landed.
    """
    fetcher = Fetcher()
    try:
        race_count = upsert_calendar(db)
        parsed = parse_all(fetcher)

        seed_slugs = {r["slug"] for r in RACES}
        for rr in parsed.race_results:
            if rr.slug and not any(_slug_matches(s, rr.slug) for s in seed_slugs):
                log.warning(
                    "standings lists race %r (%s) not in the seed calendar",
                    rr.title,
                    rr.slug,
                )

        by_nid: dict[int, Athlete] = {}
        athletes: list[Athlete] = []
        for gender, rows in (("W", parsed.W), ("M", parsed.M)):
            for row in rows:
                athlete = _upsert_athlete(db, row, gender, by_nid)
                _upsert_standing(db, athlete, row.official_points, row.rank_diff)
                athletes.append(athlete)
        _mark_completed(db)
        _scrape_start_lists(db, fetcher)
        recompute(db, warn_mismatch=False)
        db.commit()
        total = len(athletes)
        log.info(
            "committed %d races and %d athletes (official points + ranks)",
            race_count,
            total,
        )

        if pages_only:
            log.warning("pages-only scrape: athlete result points not fetched")
            return total, race_count

        for i, athlete in enumerate(athletes, start=1):
            try:
                for ar in fetch_athlete(fetcher, athlete.slug):
                    race = _match_seed_race(
                        db,
                        slug=ar.race_slug,
                        title=ar.event_title,
                        distance=ar.distance,
                        gender=athlete.gender,
                    )
                    if race is None:
                        continue
                    result = db.scalar(
                        select(Result).where(
                            Result.athlete_id == athlete.id,
                            Result.race_id == race.id,
                        )
                    )
                    if result is None:
                        result = Result(athlete_id=athlete.id, race_id=race.id)
                        db.add(result)
                    result.points = ar.points
                db.commit()
            except Exception:
                db.rollback()
                log.exception("failed on athlete page %s", athlete.slug)
            if i % 50 == 0 or i == total:
                # refresh completion + standings periodically so the site
                # converges instead of jumping at the end
                _mark_completed(db)
                recompute(db, warn_mismatch=(i == total))
                db.commit()
                log.info("athlete pages %d/%d (standings refreshed)", i, total)

        log.info("scrape complete: %d athletes, %d races", total, race_count)
        return total, race_count
    finally:
        fetcher.close()


def _race_is_done(race: Race, today: date, scored_race_ids: set[int]) -> bool:
    """A race counts as done — and so drops out of every athlete's ceiling —
    once its calendar date has passed. Points scored before the listed date
    (timezones, early publishing) also count, but the date is the primary
    signal: a past race whose points the standings haven't published yet must
    not be treated as still winnable."""
    return race.date < today or race.id in scored_race_ids


def _mark_completed(db: Session) -> None:
    today = date.today()
    scored = set(
        db.scalars(
            select(Result.race_id).where(Result.points.is_not(None)).distinct()
        )
    )
    for race in db.scalars(select(Race).where(Race.season == SEASON)):
        race.status = (
            "completed" if _race_is_done(race, today, scored) else "upcoming"
        )
    db.flush()


def _scrape_start_lists(db: Session, fetcher: Fetcher) -> None:
    """Fetch the published pro start lists and record who is on each remaining
    race. Only upcoming races are gated; a race with no entries is not gated.

    A race can be fed by more than one list (men's + women's Kona), so entries
    are accumulated across all lists and written per race in one pass."""
    races = {
        r.slug: r
        for r in db.scalars(select(Race).where(Race.season == SEASON))
    }
    index = AthleteNameIndex(list(db.scalars(select(Athlete))))

    entries: dict[int, set[int]] = {}
    touched: set[int] = set()
    for spec in START_LISTS:
        targets = {
            g: races[slug].id
            for g, slug in spec["races"].items()
            if slug in races and races[slug].status == "upcoming"
        }
        if not targets:
            continue
        try:
            rows = fetch_start_list(fetcher, spec["url"])
        except Exception:
            log.exception("failed to fetch start list %s", spec["url"])
            continue

        touched.update(targets.values())
        name = spec["url"].rsplit("/", 1)[-1]
        matched = {g: 0 for g in targets}
        unmatched: list[str] = []
        for row in rows:
            race_id = targets.get(row.gender)
            if race_id is None:
                continue
            athlete = index.find(row.gender, row.name)
            if athlete is None:
                unmatched.append(row.name)
                continue
            if athlete.id not in entries.setdefault(race_id, set()):
                entries[race_id].add(athlete.id)
                matched[row.gender] += 1
        for g, cnt in matched.items():
            log.info("start list %s: %d %s athletes matched", name, cnt, g)
        if unmatched:
            log.info(
                "start list %s: %d names not in standings (non–Pro Series / "
                "age-group): %s",
                name,
                len(unmatched),
                ", ".join(sorted(unmatched)[:15]),
            )

    if touched:
        db.execute(
            delete(StartListEntry).where(StartListEntry.race_id.in_(touched))
        )
        for race_id, athlete_ids in entries.items():
            for athlete_id in athlete_ids:
                db.add(StartListEntry(race_id=race_id, athlete_id=athlete_id))
        db.flush()


def gating_data(db: Session) -> tuple[set[int], set[tuple[int, int]]]:
    """(race_ids that have a published start list, {(race_id, athlete_id)} on it)."""
    pairs = {
        (rid, aid)
        for rid, aid in db.execute(
            select(StartListEntry.race_id, StartListEntry.athlete_id)
        )
    }
    return {rid for rid, _ in pairs}, pairs


_CEILING_SLOTS = 5


def athlete_ceiling(
    completed: list[ScoredRace],
    remaining: list[ScoredRace],
    official_points: int,
    computed_points: int,
) -> int:
    """Best legal end-of-season total for one athlete.

    The scraped result set can be incomplete — the site serves only an
    athlete's ten most recent events — so ``official_points`` (a full best-5
    from the standings) can exceed the best-5 of what we scraped. Pad the
    visible results with synthetic entries carrying the unseen points, up to
    five results, so a maxed-out remaining race *displaces* one of them the way
    it would displace one of the athlete's real weak results, instead of
    stacking on top of a full slate (which is what inflated the ceilings)."""
    pool = list(completed)
    shortfall = official_points - computed_points
    if shortfall > 0:
        visible = sum(1 for c in pool if c.points > 0)
        n = max(1, _CEILING_SLOTS - visible)
        base, extra = divmod(shortfall, n)
        pool += [
            ScoredRace(
                id=-1 - i,
                points=base + (1 if i < extra else 0),
                is_full_im=False,
            )
            for i in range(n)
        ]
    return max(official_points, ceiling_total(pool, remaining))


def _remaining_for(
    athlete: Athlete,
    races: list[Race],
    gated_race_ids: set[int] = frozenset(),
    start_list_pairs: set[tuple[int, int]] = frozenset(),
) -> list[Race]:
    out: list[Race] = []
    for r in races:
        if r.status != "upcoming":
            continue
        if r.eligible_gender not in {athlete.gender, "both"}:
            continue
        if r.id in gated_race_ids and (r.id, athlete.id) not in start_list_pairs:
            # start list published for this race and this athlete isn't on it
            continue
        out.append(r)
    return out


def recompute(db: Session, warn_mismatch: bool = True) -> None:
    races = db.scalars(select(Race).where(Race.season == SEASON)).all()
    athletes = db.scalars(select(Athlete)).all()
    race_by_id = {r.id: r for r in races}
    gated_race_ids, start_list_pairs = gating_data(db)

    for athlete in athletes:
        results = db.scalars(
            select(Result).where(Result.athlete_id == athlete.id)
        ).all()
        completed = [
            ScoredRace(
                id=res.race_id,
                points=res.points or 0,
                is_full_im=race_by_id[res.race_id].distance == "im",
            )
            for res in results
            if res.race_id in race_by_id
            and race_by_id[res.race_id].status == "completed"
        ]
        remaining = [
            ScoredRace(id=r.id, points=r.max_points, is_full_im=r.distance == "im")
            for r in _remaining_for(
                athlete, races, gated_race_ids, start_list_pairs
            )
        ]
        computed_points = best_legal_total(completed)[0]

        standing = db.scalar(
            select(Standing).where(
                Standing.athlete_id == athlete.id, Standing.season == SEASON
            )
        )
        official = standing.official_points if standing is not None else 0
        ceiling_points = athlete_ceiling(
            completed, remaining, official, computed_points
        )

        if standing is None:
            standing = Standing(athlete_id=athlete.id, season=SEASON)
            db.add(standing)
        standing.computed_points = computed_points
        standing.ceiling_points = ceiling_points
        if (
            warn_mismatch
            and standing.official_points
            and computed_points != standing.official_points
        ):
            log.warning(
                "computed_points %s != official_points %s for %s",
                computed_points,
                standing.official_points,
                athlete.slug,
            )
    db.flush()

    for gender in ("W", "M"):
        ranked = db.scalars(
            select(Standing)
            .join(Athlete, Athlete.id == Standing.athlete_id)
            .where(Standing.season == SEASON, Athlete.gender == gender)
            .order_by(Standing.official_points.desc(), Athlete.name.asc())
        ).all()
        for i, standing in enumerate(ranked, start=1):
            standing.rank = i
    db.flush()
