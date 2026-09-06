"""start list entries

Revision ID: 002_start_lists
Revises: 001_initial
Create Date: 2026-09-06

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "002_start_lists"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "start_list_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "race_id", sa.Integer(), sa.ForeignKey("races.id"), nullable=False
        ),
        sa.Column(
            "athlete_id",
            sa.Integer(),
            sa.ForeignKey("athletes.id"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "race_id", "athlete_id", name="uq_startlist_race_athlete"
        ),
    )


def downgrade() -> None:
    op.drop_table("start_list_entries")
