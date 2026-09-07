from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Athlete, Race, Result, Standing
from app.scoring import ScoredRace, best_legal_total
from app.schemas import (
    AthleteDetailOut,
    AthleteResultOut,
    HealthOut,
    RaceOut,
    RemainingRaceOut,
    ScrapeResultOut,
    StandingOut,
)
from app.scrape.persist import (
    _remaining_for,
    athlete_ceiling,
    gating_data,
    run_scrape,
)

app = FastAPI(title="Pro Series Standings")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(ok=True)


@app.get("/api/races", response_model=list[RaceOut])
def list_races(season: int = 2026, db: Session = Depends(get_db)) -> list[RaceOut]:
    races = db.scalars(
        select(Race).where(Race.season == season).order_by(Race.date.asc())
    ).all()
    return [
        RaceOut(
            slug=r.slug,
            title=r.title,
            date=r.date.isoformat(),
            distance=r.distance,
            is_world_championship=r.is_world_championship,
            max_points=r.max_points,
            eligible_gender=r.eligible_gender,
            status=r.status,
        )
        for r in races
    ]


@app.get("/api/standings", response_model=list[StandingOut])
def list_standings(
    season: int = 2026, gender: str = "W", db: Session = Depends(get_db)
) -> list[StandingOut]:
    gender = "M" if gender == "M" else "W"
    rows = db.execute(
        select(Standing, Athlete)
        .join(Athlete, Athlete.id == Standing.athlete_id)
        .where(Standing.season == season, Athlete.gender == gender)
        .order_by(Standing.rank.asc())
    ).all()
    return [
        StandingOut(
            rank=s.rank,
            rank_diff=s.rank_diff,
            name=a.name,
            slug=a.slug,
            country_code=a.country_code,
            official_points=s.official_points,
            computed_points=s.computed_points,
            ceiling_points=s.ceiling_points,
            ceiling_delta=s.ceiling_points - s.official_points,
        )
        for s, a in rows
    ]


@app.get("/api/athletes/{slug}", response_model=AthleteDetailOut)
def athlete_detail(
    slug: str, season: int = 2026, db: Session = Depends(get_db)
) -> AthleteDetailOut:
    athlete = db.scalar(select(Athlete).where(Athlete.slug == slug))
    if athlete is None:
        raise HTTPException(status_code=404, detail="athlete not found")

    races = db.scalars(select(Race).where(Race.season == season)).all()
    race_by_id = {r.id: r for r in races}
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
    gated_race_ids, start_list_pairs = gating_data(db)
    remaining_races = _remaining_for(
        athlete, races, gated_race_ids, start_list_pairs
    )
    remaining_scored = [
        ScoredRace(id=r.id, points=r.max_points, is_full_im=r.distance == "im")
        for r in remaining_races
    ]

    computed_points, chosen = best_legal_total(completed)
    chosen_ids = {s.id for s in chosen}

    standing = db.scalar(
        select(Standing).where(
            Standing.athlete_id == athlete.id, Standing.season == season
        )
    )
    current_points = (
        standing.official_points if standing is not None else computed_points
    )
    ceiling_points = athlete_ceiling(
        completed, remaining_scored, current_points, computed_points
    )

    result_out = [
        AthleteResultOut(
            event=race_by_id[res.race_id].title,
            points=res.points,
            distance=race_by_id[res.race_id].distance,
            counts_toward_total=res.race_id in chosen_ids,
        )
        for res in results
        if res.race_id in race_by_id
        and race_by_id[res.race_id].status == "completed"
    ]

    return AthleteDetailOut(
        name=athlete.name,
        slug=athlete.slug,
        gender=athlete.gender,
        current_points=current_points,
        ceiling_points=ceiling_points,
        results=result_out,
        remaining=[
            RemainingRaceOut(slug=r.slug, title=r.title, max_points=r.max_points)
            for r in sorted(remaining_races, key=lambda r: r.date)
        ],
    )


@app.post("/api/scrape", response_model=ScrapeResultOut)
def scrape(
    x_scrape_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> ScrapeResultOut:
    if x_scrape_token != settings.scrape_token:
        raise HTTPException(status_code=401, detail="invalid scrape token")
    athletes, races = run_scrape(db)
    return ScrapeResultOut(athletes=athletes, races=races)
