from __future__ import annotations

import sys
import types

from fastapi import APIRouter

from app.core.registry import Registry, build_registry


def test_add_router_appends() -> None:
    registry = Registry()
    router = APIRouter()
    registry.add_router(router)
    assert registry.routers == [router]


def test_build_registry_imports_and_calls_register(monkeypatch) -> None:
    calls: list[Registry] = []
    fake_module = types.ModuleType("app.modules._fake_test_module")

    def register(registry: Registry) -> None:
        calls.append(registry)
        registry.add_router(APIRouter(prefix="/fake"))

    fake_module.register = register  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.modules._fake_test_module", fake_module)

    registry = build_registry(["app.modules._fake_test_module"])

    assert len(calls) == 1
    assert calls[0] is registry
    assert len(registry.routers) == 1
    assert registry.routers[0].prefix == "/fake"


def test_build_registry_with_no_modules_returns_empty_registry() -> None:
    registry = build_registry([])
    assert registry.routers == []
