from openrouter_cli import sdk_adapter
from openrouter_cli.app import app
from tests.fakes import FakeAdapter, build_adapter_factory


def _patch(monkeypatch, fake: FakeAdapter):
    monkeypatch.setattr(sdk_adapter, "build_adapter", build_adapter_factory(fake))


def test_models_list_passes_modality_filters_to_adapter(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(chat_models=[{"id": "google/gemini-3-pro", "name": "Gemini 3 Pro"}])
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["models", "list", "--input-modality", "video"])

    assert result.exit_code == 0, result.output
    assert "google/gemini-3-pro" in result.output
    call = fake.calls[0]
    assert call[0] == "list_chat_models"
    assert call[1]["input_modalities"] == "video"


def test_models_list_limit(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(chat_models=[{"id": f"m/{i}"} for i in range(10)])
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["--json", "models", "list", "--limit", "3"])

    import json

    payload = json.loads(result.output)
    assert len(payload["models"]) == 3
