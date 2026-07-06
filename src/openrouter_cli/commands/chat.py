from typing import Optional

import typer

from openrouter_cli.config import get_api_key, get_base_url, get_chat_model, get_run_ctx
from openrouter_cli.output import echo, emit_result, handle_errors
from openrouter_cli import sdk_adapter


@handle_errors
def chat(
    prompt: str = typer.Argument(..., help="Message to send to the model."),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Model to use, e.g. openai/gpt-5. Defaults to $OPENROUTER_MODEL or openrouter/auto."
    ),
    temperature: Optional[float] = typer.Option(None, "--temperature"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens"),
) -> None:
    """Send a plain text prompt to a chat model - no file involved.

    Examples:
      orouter chat "What is the capital of France?"
      orouter chat "Write a haiku about kites" --model google/gemini-3-pro
    """
    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)
    resolved_model = get_chat_model(model)

    content_parts = [{"type": "text", "text": prompt}]

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
