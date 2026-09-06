from pydantic import BaseModel


class HealthOut(BaseModel):
    ok: bool


class RaceOut(BaseModel):
    slug: str
    title: str
    date: str
    distance: str
    is_world_championship: bool
    max_points: int
    eligible_gender: str
    status: str


class StandingOut(BaseModel):
    rank: int
    rank_diff: int | None
    name: str
    slug: str
    country_code: str | None
    official_points: int
    computed_points: int
    ceiling_points: int
    ceiling_delta: int


class AthleteResultOut(BaseModel):
    event: str
    points: int | None
    distance: str
    counts_toward_total: bool


class RemainingRaceOut(BaseModel):
    slug: str
    title: str
    max_points: int


class AthleteDetailOut(BaseModel):
    name: str
    slug: str
    gender: str
    current_points: int
    ceiling_points: int
    results: list[AthleteResultOut]
    remaining: list[RemainingRaceOut]


class ScrapeResultOut(BaseModel):
    athletes: int
    races: int
