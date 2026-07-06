from typing import Optional

import typer

from openrouter_cli.config import get_api_key, get_base_url, get_run_ctx
from openrouter_cli.output import echo, emit_result, handle_errors
from openrouter_cli import sdk_adapter

app = typer.Typer(help="Discover chat/vision models.", no_args_is_help=True)


@app.command("list")
@handle_errors
def list_models(
    input_modality: Optional[str] = typer.Option(
        None, "--input-modality", help="Filter by input modality, e.g. image, video, audio, text, file."
    ),
    output_modality: Optional[str] = typer.Option(
        None, "--output-modality", help="Filter by output modality, e.g. text, image."
    ),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Free-text search over model name/id."),
    limit: Optional[int] = typer.Option(None, "--limit", help="Only show the first N results."),
) -> None:
    """List chat/vision models available on OpenRouter, so you can pick a --model before running `analyze`.

    Examples:
      orouter models list --input-modality video
      orouter models list --query gemini
      orouter --json models list --limit 5
    """
    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)

    with sdk_adapter.build_adapter(api_key, get_base_url(run_ctx)) as adapter:
        items = adapter.list_chat_models(
            input_modalities=input_modality, output_modalities=output_modality, q=query
        )

    if limit is not None:
        items = items[:limit]

    def render(data):
        for m in data["models"]:
            echo(f"{m.get('id')}  {m.get('name', '')}")

    emit_result({"models": items}, render)
