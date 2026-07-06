from typing import Optional

import typer

from openrouter_cli import mime_utils
from openrouter_cli.config import get_api_key, get_base_url, get_chat_model, get_run_ctx
from openrouter_cli.output import echo, emit_result, handle_errors
from openrouter_cli import sdk_adapter


@handle_errors
def analyze(
    file: str = typer.Argument(
        ..., help="Local path or http(s) URL to an image, video, audio, or PDF file."
    ),
    prompt: str = typer.Option(..., "--prompt", "-p", help="What to ask the model about the file."),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Model to use, e.g. google/gemini-3-pro. Defaults to $OPENROUTER_MODEL or openrouter/auto."
    ),
    type_: Optional[str] = typer.Option(
        None, "--type", help="Override content-type auto-detection: image, video, audio, or file."
    ),
    temperature: Optional[float] = typer.Option(None, "--temperature"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens"),
) -> None:
    """Analyze a local or remote multimodal file (image/video/audio/PDF) with a vision-capable model.

    Examples:
      orouter analyze kite.mp4 --prompt "Analyze flight physics" --model google/gemini-3-pro
      orouter analyze ./invoice.pdf --prompt "Summarize the line items" --type file
      orouter analyze https://example.com/photo.jpg --prompt "What is in this image?"
    """
    kind, mime = mime_utils.detect_kind(file, override=type_)

    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)
    resolved_model = get_chat_model(model)

    content_part = mime_utils.build_content_part(file, kind, mime)
    content_parts = [{"type": "text", "text": prompt}, content_part]

    with sdk_adapter.build_adapter(api_key, get_base_url(run_ctx)) as adapter:
        result = adapter.chat_send(
            model=resolved_model,
            content_parts=content_parts,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def render(data):
        echo(data["text"])

    emit_result({"model": result.model, "text": result.text, "raw": result.raw}, render)
