# backend/app/modules/combat/__init__.py
from __future__ import annotations

from app.core.registry import Registry
from app.modules.combat.routes import router


def register(registry: Registry) -> None:
    registry.add_router(router)
