from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BestiaryMonster(Base):
    __tablename__ = "bestiary_monster"
    __table_args__ = (
        UniqueConstraint("campaign_id", "slug", name="uq_bestiary_monster_campaign_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaign.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), nullable=False)
    statblock: Mapped[str] = mapped_column(Text, nullable=False)
    # Denormalized from statblock.creature_type / statblock.challenge_rating,
    # kept in sync by service.py on every create/update, so list/search/filter
    # run as real SQL WHERE/ORDER BY instead of parsing the JSON blob per row.
    creature_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    challenge_rating: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500))
    is_favorite: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )
    # Soft cross-module reference to a future content.creature row — no DB FK
    # (module independence; content/ doesn't exist yet either).
    cloned_from_content_id: Mapped[int | None] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), nullable=False
    )
