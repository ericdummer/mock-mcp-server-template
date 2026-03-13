"""
Test configuration management.
"""

import pytest

from app.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """Ensure get_settings() cache does not leak between tests."""
    get_settings.cache_clear()


def test_settings_defaults() -> None:
    """Settings should have sensible defaults with no required environment variables."""
    settings = Settings(_env_file=None)
    assert settings.app_name == "Mock MCP Server"
    assert settings.debug is False
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.api_key_header == "X-Api-Key"
    assert settings.log_level == "INFO"


def test_settings_loads_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEBUG", "true")
    settings = Settings()
    assert settings.debug is True


def test_get_settings_is_cached() -> None:
    first = get_settings()
    second = get_settings()
    assert first is second
