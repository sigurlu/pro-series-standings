"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-09-05

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "athletes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ironman_nid", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("gender", sa.String(length=1), nullable=False),
        sa.UniqueConstraint("ironman_nid", name="uq_athletes_ironman_nid"),
        sa.UniqueConstraint("slug", name="uq_athletes_slug"),
    )
    op.create_table(
        "races",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("distance", sa.String(), nullable=False),
        sa.Column("is_world_championship", sa.Boolean(), nullable=False),
        sa.Column("max_points", sa.Integer(), nullable=False),
        sa.Column("eligible_gender", sa.String(length=4), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.UniqueConstraint("season", "slug", name="uq_race_season_slug"),
    )
    op.create_index("ix_races_slug", "races", ["slug"])
    op.create_table(
        "results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("athlete_id", sa.Integer(), sa.ForeignKey("athletes.id"), nullable=False),
        sa.Column("race_id", sa.Integer(), sa.ForeignKey("races.id"), nullable=False),
        sa.Column("points", sa.Integer(), nullable=True),
        sa.Column("finish_time", sa.String(), nullable=True),
        sa.Column("finish_rank", sa.Integer(), nullable=True),
        sa.UniqueConstraint("athlete_id", "race_id", name="uq_result_athlete_race"),
    )
    op.create_table(
        "standings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("athlete_id", sa.Integer(), sa.ForeignKey("athletes.id"), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("official_points", sa.Integer(), nullable=False),
        sa.Column("computed_points", sa.Integer(), nullable=False),
        sa.Column("ceiling_points", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("rank_diff", sa.Integer(), nullable=True),
        sa.UniqueConstraint("athlete_id", "season", name="uq_standing_athlete_season"),
    )


def downgrade() -> None:
    op.drop_table("standings")
    op.drop_table("results")
    op.drop_index("ix_races_slug", table_name="races")
    op.drop_table("races")
    op.drop_table("athletes")
