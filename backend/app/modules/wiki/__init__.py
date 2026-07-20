# backend/app/modules/wiki/__init__.py
from __future__ import annotations

from app.core.registry import Registry
from app.modules.wiki.routes import router


def register(registry: Registry) -> None:
    registry.add_router(router)
