from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

DIAGONAL_RULES = ("chebyshev", "five_ten_five", "euclidean", "manhattan")
TOKEN_LAYERS = ("tokens", "dm")
TOKEN_KINDS = ("disc", "image")


class Map(Base):
    __tablename__ = "map"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaign.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    image_path: Mapped[str | None] = mapped_column(String(500))
    image_w: Mapped[int | None] = mapped_column(Integer)
    image_h: Mapped[int | None] = mapped_column(Integer)
    grid_size_px: Mapped[int] = mapped_column(
        Integer, default=70, server_default="70", nullable=False
    )
    grid_offset_x: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    grid_offset_y: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    grid_visible: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", nullable=False
    )
    feet_per_square: Mapped[int] = mapped_column(
        Integer, default=5, server_default="5", nullable=False
    )
    diagonal_rule: Mapped[str] = mapped_column(
        String(20), default="chebyshev", server_default="chebyshev", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )

    tokens: Mapped[list[Token]] = relationship(
        back_populates="map", cascade="all, delete-orphan", order_by="Token.id"
    )
    fog_regions: Mapped[list[FogRegion]] = relationship(
        back_populates="map",
        cascade="all, delete-orphan",
        order_by="FogRegion.order_index, FogRegion.id",
    )


class Token(Base):
    __tablename__ = "token"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    map_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("map.id", ondelete="CASCADE"), index=True, nullable=False
    )
    layer: Mapped[str] = mapped_column(
        String(20), default="tokens", server_default="tokens", nullable=False
    )
    kind: Mapped[str] = mapped_column(
        String(20), default="disc", server_default="disc", nullable=False
    )
    x: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    y: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    size_squares: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
    )
    color: Mapped[str] = mapped_column(
        String(20), default="#888888", server_default="#888888", nullable=False
    )
    image_path: Mapped[str | None] = mapped_column(String(500))
    name: Mapped[str] = mapped_column(String(200), default="", server_default="", nullable=False)
    hp_current: Mapped[int | None] = mapped_column(Integer)
    hp_max: Mapped[int | None] = mapped_column(Integer)
    hp_visible_to_players: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )
    visible_to_players: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", nullable=False
    )
    status_markers_json: Mapped[str] = mapped_column(
        Text, default="[]", server_default="[]", nullable=False
    )
    is_pc: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    npc_id: Mapped[int | None] = mapped_column(Integer, index=True)
    combatant_id: Mapped[int | None] = mapped_column(Integer, index=True)

    map: Mapped[Map] = relationship(back_populates="tokens")


class FogRegion(Base):
    __tablename__ = "fog_region"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    map_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("map.id", ondelete="CASCADE"), index=True, nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)  # 'reveal' | 'hide'
    geometry_json: Mapped[str] = mapped_column(Text, nullable=False)

    map: Mapped[Map] = relationship(back_populates="fog_regions")
