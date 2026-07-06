import json

from openrouter_cli import sdk_adapter
from openrouter_cli.app import app
from openrouter_cli.sdk_adapter import TranscriptionResult
from tests.fakes import FakeAdapter, build_adapter_factory


def _patch(monkeypatch, fake: FakeAdapter):
    monkeypatch.setattr(sdk_adapter, "build_adapter", build_adapter_factory(fake))


def test_transcribe_builds_input_audio_and_prints_text(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(transcription_result=TranscriptionResult(text="hello world", raw={}))
    _patch(monkeypatch, fake)
    clip = tmp_path / "clip.mp3"
    clip.write_bytes(b"fake")

    result = runner.invoke(app, ["audio", "transcribe", str(clip), "--model", "openai/whisper-1"])

    assert result.exit_code == 0, result.output
    assert "hello world" in result.output
    call = fake.calls[0]
    assert call[0] == "audio_transcribe"
    assert call[1]["model"] == "openai/whisper-1"
    assert call[1]["input_audio"]["format"] == "mp3"
    assert "data" in call[1]["input_audio"]


def test_transcribe_passes_language(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(transcription_result=TranscriptionResult(text="bonjour", raw={}))
    _patch(monkeypatch, fake)
    clip = tmp_path / "clip.mp3"
    clip.write_bytes(b"fake")

    result = runner.invoke(
        app, ["audio", "transcribe", str(clip), "--model", "openai/whisper-1", "--language", "fr"]
    )

    assert result.exit_code == 0, result.output
    assert fake.calls[0][1]["language"] == "fr"


def test_transcribe_missing_model_exits_2(runner, api_key_env, monkeypatch, tmp_path):
    monkeypatch.delenv("OPENROUTER_STT_MODEL", raising=False)
    clip = tmp_path / "clip.mp3"
    clip.write_bytes(b"fake")

    result = runner.invoke(app, ["audio", "transcribe", str(clip)])

    assert result.exit_code == 2
    assert "OPENROUTER_STT_MODEL" in result.output


def test_transcribe_missing_api_key_exits_2(runner, monkeypatch, tmp_path):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    clip = tmp_path / "clip.mp3"
    clip.write_bytes(b"fake")

    result = runner.invoke(app, ["audio", "transcribe", str(clip), "--model", "openai/whisper-1"])

    assert result.exit_code == 2


def test_speak_writes_output_file(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(audio_content=b"mp3bytes")
    _patch(monkeypatch, fake)
    out = tmp_path / "hello.mp3"

    result = runner.invoke(
        app,
        [
            "audio", "speak", "Hello from Lahore", "--voice", "alloy", "--model", "openai/tts-1",
            "--output", str(out),
        ],
    )

    assert result.exit_code == 0, result.output
    assert out.read_bytes() == b"mp3bytes"
    call = fake.calls[0]
    assert call[0] == "audio_speak"
    assert call[1]["voice"] == "alloy"
    assert call[1]["response_format"] == "mp3"


def test_speak_missing_model_exits_2(runner, api_key_env, monkeypatch, tmp_path):
    monkeypatch.delenv("OPENROUTER_TTS_MODEL", raising=False)
    out = tmp_path / "hello.mp3"

    result = runner.invoke(app, ["audio", "speak", "hi", "--voice", "alloy", "--output", str(out)])

    assert result.exit_code == 2
    assert "OPENROUTER_TTS_MODEL" in result.output
    assert not out.exists()


def test_speak_json_output(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(audio_content=b"mp3bytes")
    _patch(monkeypatch, fake)
    out = tmp_path / "hello.mp3"

    result = runner.invoke(
        app,
        ["--json", "audio", "speak", "hi", "--voice", "alloy", "--model", "openai/tts-1", "--output", str(out)],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["file"] == str(out)
