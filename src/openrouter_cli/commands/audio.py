from pathlib import Path
from typing import Optional

import typer

from openrouter_cli import io_utils, mime_utils
from openrouter_cli.config import get_api_key, get_base_url, get_run_ctx, get_stt_model, get_tts_model
from openrouter_cli.output import echo, emit_result, handle_errors
from openrouter_cli import sdk_adapter

app = typer.Typer(help="Transcribe and synthesize audio.", no_args_is_help=True)


@app.command("transcribe")
@handle_errors
def transcribe(
    file: str = typer.Argument(..., help="Local path or http(s) URL to an audio file."),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Speech-to-text model to use. Defaults to $OPENROUTER_STT_MODEL."
    ),
    language: Optional[str] = typer.Option(None, "--language", help="ISO language hint, e.g. en, ur."),
) -> None:
    """Transcribe a local or remote audio file to text.

    Examples:
      orouter audio transcribe voice_note.mp3 --model openai/whisper-1
      orouter audio transcribe https://example.com/clip.wav --language en
    """
    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)
    resolved_model = get_stt_model(model)

    _, mime = mime_utils.detect_kind(file, override="audio")
    input_audio = mime_utils.build_content_part(file, "audio", mime)["input_audio"]

    with sdk_adapter.build_adapter(api_key, get_base_url(run_ctx)) as adapter:
        result = adapter.audio_transcribe(model=resolved_model, input_audio=input_audio, language=language)

    def render(data):
        echo(data["text"])

    emit_result({"model": resolved_model, "text": result.text, "raw": result.raw}, render)


@app.command("speak")
@handle_errors
def speak(
    text: str = typer.Argument(..., help="Text to synthesize."),
    output: Path = typer.Option(..., "--output", "-o", help="Where to save the generated audio."),
    voice: str = typer.Option(..., "--voice", help="Voice to use - options are model-dependent."),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Text-to-speech model to use. Defaults to $OPENROUTER_TTS_MODEL."
    ),
    response_format: str = typer.Option("mp3", "--format", help="mp3 or pcm."),
    speed: Optional[float] = typer.Option(None, "--speed"),
) -> None:
    """Synthesize speech from text.

    Examples:
      orouter audio speak "Hello from Lahore" --voice alloy --model openai/tts-1 --output hello.mp3
    """
    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)
    resolved_model = get_tts_model(model)

    with sdk_adapter.build_adapter(api_key, get_base_url(run_ctx)) as adapter:
        data = adapter.audio_speak(
            model=resolved_model, text=text, voice=voice, response_format=response_format, speed=speed
        )

    io_utils.write_bytes(output, data)

    def render(result):
        echo(f"Saved {result['file']}")

    emit_result({"model": resolved_model, "file": str(output)}, render)
