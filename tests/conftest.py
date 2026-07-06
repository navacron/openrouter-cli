import pytest
from typer.testing import CliRunner

from openrouter_cli import config


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def _reset_run_ctx():
    config._run_ctx = None
    yield
    config._run_ctx = None


@pytest.fixture
def api_key_env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
