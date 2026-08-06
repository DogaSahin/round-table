"""bestiary monster type and cr columns

Revision ID: 655476c0c228
Revises: ac8a6dd8a6ad
Create Date: 2026-07-29 00:28:47.051870

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '655476c0c228'
down_revision: str | None = 'ac8a6dd8a6ad'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("bestiary_monster")
    op.create_table(
        "bestiary_monster",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("statblock", sa.Text(), nullable=False),
        sa.Column("creature_type", sa.String(length=100), nullable=False),
        sa.Column("challenge_rating", sa.Float(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("is_favorite", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("cloned_from_content_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaign.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id", "slug", name="uq_bestiary_monster_campaign_slug"),
    )
    op.create_index(
        op.f("ix_bestiary_monster_campaign_id"), "bestiary_monster", ["campaign_id"], unique=False
    )
    op.create_index(
        op.f("ix_bestiary_monster_cloned_from_content_id"),
        "bestiary_monster",
        ["cloned_from_content_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bestiary_monster_creature_type"), "bestiary_monster", ["creature_type"], unique=False
    )
    op.create_index(
        op.f("ix_bestiary_monster_challenge_rating"),
        "bestiary_monster",
        ["challenge_rating"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("bestiary_monster")
    op.create_table(
        "bestiary_monster",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("statblock", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("is_favorite", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("cloned_from_content_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaign.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id", "slug", name="uq_bestiary_monster_campaign_slug"),
    )
    op.create_index(
        op.f("ix_bestiary_monster_campaign_id"), "bestiary_monster", ["campaign_id"], unique=False
    )
    op.create_index(
        op.f("ix_bestiary_monster_cloned_from_content_id"),
        "bestiary_monster",
        ["cloned_from_content_id"],
        unique=False,
    )
