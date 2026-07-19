# backend/tests/test_config.py
from __future__ import annotations

from app.core.config import get_settings


def test_defaults_when_no_env_set(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.database_url == "sqlite:///./data/roundtable.db"
    assert settings.enabled_modules == [
        "app.modules.dice",
        "app.modules.sessions",
        "app.modules.factions",
        "app.modules.npcs",
    ]
    assert settings.cors_origins == ["http://localhost:5173"]


def test_cors_origins_parsed_from_comma_separated_env(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:4173")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.cors_origins == ["http://localhost:5173", "http://localhost:4173"]


def test_enabled_modules_parsed_from_comma_separated_env(monkeypatch) -> None:
    monkeypatch.setenv("ENABLED_MODULES", "app.modules.dice,app.modules.factions")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.enabled_modules == ["app.modules.dice", "app.modules.factions"]


def test_get_settings_is_cached(monkeypatch) -> None:
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second


def test_media_dir_created_on_settings_construction(tmp_path, monkeypatch) -> None:
    target = tmp_path / "media-out"
    monkeypatch.setenv("MEDIA_DIR", str(target))
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.media_dir == target
    assert target.is_dir()
