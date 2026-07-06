import json

from openrouter_cli import sdk_adapter
from openrouter_cli.app import app
from openrouter_cli.sdk_adapter import ChatAnalysisResult
from tests.fakes import FakeAdapter, build_adapter_factory


def _patch(monkeypatch, fake: FakeAdapter):
    monkeypatch.setattr(sdk_adapter, "build_adapter", build_adapter_factory(fake))


def test_analyze_image_builds_image_content_part(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(chat_result=ChatAnalysisResult(text="a cat", model="m", raw={}))
    _patch(monkeypatch, fake)

    img = tmp_path / "a.jpg"
    img.write_bytes(b"fake")

    result = runner.invoke(app, ["analyze", str(img), "--prompt", "what is this"])

    assert result.exit_code == 0, result.output
    assert "a cat" in result.output
    call = fake.calls[0]
    assert call[0] == "chat_send"
    parts = call[1]["content_parts"]
    assert parts[0] == {"type": "text", "text": "what is this"}
    assert parts[1]["type"] == "image_url"


def test_analyze_video_builds_video_content_part(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(chat_result=ChatAnalysisResult(text="flight physics", model="m", raw={}))
    _patch(monkeypatch, fake)

    vid = tmp_path / "kite.mp4"
    vid.write_bytes(b"fake")

    result = runner.invoke(
        app, ["analyze", str(vid), "--prompt", "Analyze flight physics", "--model", "google/gemini-3-pro"]
    )

    assert result.exit_code == 0, result.output
    parts = fake.calls[0][1]["content_parts"]
    assert parts[1]["type"] == "video_url"
    assert fake.calls[0][1]["model"] == "google/gemini-3-pro"


def test_analyze_audio_builds_input_audio_part(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(chat_result=ChatAnalysisResult(text="ok", model="m", raw={}))
    _patch(monkeypatch, fake)

    aud = tmp_path / "clip.mp3"
    aud.write_bytes(b"fake")

    result = runner.invoke(app, ["analyze", str(aud), "--prompt", "transcribe"])

    assert result.exit_code == 0, result.output
    parts = fake.calls[0][1]["content_parts"]
    assert parts[1]["type"] == "input_audio"


def test_analyze_file_builds_file_part(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(chat_result=ChatAnalysisResult(text="summary", model="m", raw={}))
    _patch(monkeypatch, fake)

    doc = tmp_path / "doc.pdf"
    doc.write_bytes(b"fake")

    result = runner.invoke(app, ["analyze", str(doc), "--prompt", "summarize"])

    assert result.exit_code == 0, result.output
    parts = fake.calls[0][1]["content_parts"]
    assert parts[1]["type"] == "file"


def test_analyze_missing_api_key_exits_2(runner, monkeypatch, tmp_path):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    img = tmp_path / "a.jpg"
    img.write_bytes(b"fake")

    result = runner.invoke(app, ["analyze", str(img), "--prompt", "hi"])

    assert result.exit_code == 2
    assert "OPENROUTER_API_KEY" in result.output


def test_analyze_missing_api_key_json_mode(runner, monkeypatch, tmp_path):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    img = tmp_path / "a.jpg"
    img.write_bytes(b"fake")

    result = runner.invoke(app, ["--json", "analyze", str(img), "--prompt", "hi"])

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["error"]["type"] == "ConfigError"


def test_analyze_json_mode_output(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(chat_result=ChatAnalysisResult(text="a cat", model="m", raw={"id": "x"}))
    _patch(monkeypatch, fake)
    img = tmp_path / "a.jpg"
    img.write_bytes(b"fake")

    result = runner.invoke(app, ["--json", "analyze", str(img), "--prompt", "what is this"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["text"] == "a cat"
