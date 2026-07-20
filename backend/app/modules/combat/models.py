# backend/app/modules/combat/models.py
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

CONDITIONS = (
    "blinded",
    "charmed",
    "deafened",
    "frightened",
    "grappled",
    "incapacitated",
    "invisible",
    "paralyzed",
    "petrified",
    "poisoned",
    "prone",
    "restrained",
    "stunned",
    "unconscious",
)


class Encounter(Base):
    __tablename__ = "encounter"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaign.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    round: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    active_combatant_id: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )

    combatants: Mapped[list[Combatant]] = relationship(
        back_populates="encounter",
        cascade="all, delete-orphan",
        order_by="Combatant.sort_order, Combatant.id",
    )


class Combatant(Base):
    __tablename__ = "combatant"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    encounter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("encounter.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    initiative: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    hp_current: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    hp_max: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    ac: Mapped[int | None] = mapped_column(Integer)
    conditions_json: Mapped[str] = mapped_column(
        Text, default="[]", server_default="[]", nullable=False
    )
    concentration: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    is_pc: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    visible_to_players: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )
    npc_id: Mapped[int | None] = mapped_column(Integer, index=True)
    token_id: Mapped[int | None] = mapped_column(Integer, index=True)

    encounter: Mapped[Encounter] = relationship(back_populates="combatants")
