import json

from openrouter_cli import sdk_adapter
from openrouter_cli.app import app
from openrouter_cli.sdk_adapter import ChatAnalysisResult
from tests.fakes import FakeAdapter, build_adapter_factory


def _patch(monkeypatch, fake: FakeAdapter):
    monkeypatch.setattr(sdk_adapter, "build_adapter", build_adapter_factory(fake))


def test_chat_sends_plain_text_content_part(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(chat_result=ChatAnalysisResult(text="Paris", model="m", raw={}))
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["chat", "What is the capital of France?"])

    assert result.exit_code == 0, result.output
    assert "Paris" in result.output
    call = fake.calls[0]
    assert call[0] == "chat_send"
    assert call[1]["content_parts"] == [{"type": "text", "text": "What is the capital of France?"}]


def test_chat_uses_explicit_model(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(chat_result=ChatAnalysisResult(text="haiku", model="m", raw={}))
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["chat", "Write a haiku about kites", "--model", "google/gemini-3-pro"])

    assert result.exit_code == 0, result.output
    assert fake.calls[0][1]["model"] == "google/gemini-3-pro"


def test_chat_missing_api_key_exits_2(runner, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    result = runner.invoke(app, ["chat", "hi"])

    assert result.exit_code == 2
    assert "OPENROUTER_API_KEY" in result.output


def test_chat_json_mode_output(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(chat_result=ChatAnalysisResult(text="Paris", model="m", raw={"id": "x"}))
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["--json", "chat", "capital of France?"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["text"] == "Paris"
