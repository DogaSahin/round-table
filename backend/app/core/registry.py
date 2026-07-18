from __future__ import annotations

import importlib
from dataclasses import dataclass, field

from fastapi import APIRouter


@dataclass
class Registry:
    """Composition root modules register into. Deliberately minimal: routers
    only. The old app's nav items / dashboard cards / entity-jump providers
    were HTML-shell concerns that don't carry forward — the Vue SPA composes
    cross-module views itself by calling each module's JSON API."""

    routers: list[APIRouter] = field(default_factory=list)

    def add_router(self, router: APIRouter) -> None:
        self.routers.append(router)


def build_registry(enabled_modules: list[str]) -> Registry:
    registry = Registry()
    for dotted_path in enabled_modules:
        module = importlib.import_module(dotted_path)
        module.register(registry)
    return registry
