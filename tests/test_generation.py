from openrouter_cli import sdk_adapter
from openrouter_cli.app import app
from tests.fakes import FakeAdapter, build_adapter_factory


def _patch(monkeypatch, fake: FakeAdapter):
    monkeypatch.setattr(sdk_adapter, "build_adapter", build_adapter_factory(fake))


def test_generation_info(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(
        generation_info={
            "id": "gen-abc123",
            "model": "anthropic/claude-sonnet-5",
            "provider_name": "Anthropic",
            "total_cost": 0.0042,
            "tokens_prompt": 100,
            "tokens_completion": 50,
            "generation_time": 1.23,
        }
    )
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["generation", "info", "gen-abc123"])

    assert result.exit_code == 0, result.output
    assert "gen-abc123" in result.output
    assert "anthropic/claude-sonnet-5" in result.output
    assert fake.calls[0] == ("get_generation", {"generation_id": "gen-abc123"})
