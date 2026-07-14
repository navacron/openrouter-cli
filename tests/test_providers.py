from openrouter_cli import sdk_adapter
from openrouter_cli.app import app
from tests.fakes import FakeAdapter, build_adapter_factory


def _patch(monkeypatch, fake: FakeAdapter):
    monkeypatch.setattr(sdk_adapter, "build_adapter", build_adapter_factory(fake))


def test_providers_list(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(providers=[{"slug": "google-ai-studio", "name": "Google AI Studio"}])
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["providers", "list"])

    assert result.exit_code == 0, result.output
    assert "google-ai-studio" in result.output
    assert "Google AI Studio" in result.output
