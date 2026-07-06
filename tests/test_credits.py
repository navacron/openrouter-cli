import json

from openrouter_cli import sdk_adapter
from openrouter_cli.app import app
from openrouter_cli.sdk_adapter import CreditsInfo
from tests.fakes import FakeAdapter, build_adapter_factory


def _patch(monkeypatch, fake: FakeAdapter):
    monkeypatch.setattr(sdk_adapter, "build_adapter", build_adapter_factory(fake))


def test_credits_prints_balance(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(credits_info=CreditsInfo(total_credits=100.0, total_usage=25.5, balance=74.5, raw={}))
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["credits"])

    assert result.exit_code == 0, result.output
    assert "100.0" in result.output
    assert "25.5" in result.output
    assert "74.5" in result.output


def test_credits_json_output(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(credits_info=CreditsInfo(total_credits=100.0, total_usage=25.5, balance=74.5, raw={}))
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["--json", "credits"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload == {"total_credits": 100.0, "total_usage": 25.5, "balance": 74.5}


def test_credits_missing_api_key_exits_2(runner, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    result = runner.invoke(app, ["credits"])

    assert result.exit_code == 2
