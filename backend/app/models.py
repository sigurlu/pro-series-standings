from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Athlete(Base):
    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(primary_key=True)
    ironman_nid: Mapped[int] = mapped_column(Integer, unique=True)
    slug: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    gender: Mapped[str] = mapped_column(String(1))

    results: Mapped[list["Result"]] = relationship(back_populates="athlete")
    standings: Mapped[list["Standing"]] = relationship(back_populates="athlete")


class Race(Base):
    __tablename__ = "races"
    __table_args__ = (UniqueConstraint("season", "slug", name="uq_race_season_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    season: Mapped[int] = mapped_column(Integer)
    slug: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    date: Mapped[date] = mapped_column(Date)
    distance: Mapped[str] = mapped_column(String)
    is_world_championship: Mapped[bool] = mapped_column(default=False)
    max_points: Mapped[int] = mapped_column(Integer)
    eligible_gender: Mapped[str] = mapped_column(String(4))
    status: Mapped[str] = mapped_column(String, default="upcoming")

    results: Mapped[list["Result"]] = relationship(back_populates="race")


class Result(Base):
    __tablename__ = "results"
    __table_args__ = (
        UniqueConstraint("athlete_id", "race_id", name="uq_result_athlete_race"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"))
    race_id: Mapped[int] = mapped_column(ForeignKey("races.id"))
    points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    finish_time: Mapped[str | None] = mapped_column(String, nullable=True)
    finish_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)

    athlete: Mapped["Athlete"] = relationship(back_populates="results")
    race: Mapped["Race"] = relationship(back_populates="results")


class StartListEntry(Base):
    """An athlete confirmed on the published start list for an upcoming race.
    Once any entries exist for a race, that race is gated: it only enters the
    ceiling of athletes who appear on its list."""

    __tablename__ = "start_list_entries"
    __table_args__ = (
        UniqueConstraint(
            "race_id", "athlete_id", name="uq_startlist_race_athlete"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    race_id: Mapped[int] = mapped_column(ForeignKey("races.id"))
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"))


class Standing(Base):
    __tablename__ = "standings"
    __table_args__ = (
        UniqueConstraint("athlete_id", "season", name="uq_standing_athlete_season"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"))
    season: Mapped[int] = mapped_column(Integer)
    official_points: Mapped[int] = mapped_column(Integer, default=0)
    computed_points: Mapped[int] = mapped_column(Integer, default=0)
    ceiling_points: Mapped[int] = mapped_column(Integer, default=0)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    rank_diff: Mapped[int | None] = mapped_column(Integer, nullable=True)

    athlete: Mapped["Athlete"] = relationship(back_populates="standings")
