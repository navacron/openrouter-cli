import sys
from typing import Optional

import typer

from openrouter_cli.config import get_api_key, get_base_url, get_embedding_model, get_run_ctx
from openrouter_cli.errors import ValidationError
from openrouter_cli.output import echo, emit_result, handle_errors
from openrouter_cli import sdk_adapter


@handle_errors
def embed(
    input_: list[str] = typer.Option(
        [], "--input", "-i", help="Text to embed. Repeatable for multiple inputs. Reads stdin if omitted."
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Embedding model to use. Defaults to $OPENROUTER_EMBEDDING_MODEL."
    ),
    dimensions: Optional[int] = typer.Option(
        None, "--dimensions", help="Target embedding dimensionality, if the model supports it."
    ),
    encoding_format: Optional[str] = typer.Option(None, "--encoding-format", help="float or base64."),
    input_type: Optional[str] = typer.Option(
        None, "--input-type", help="Provider-specific hint, e.g. search_document, search_query."
    ),
) -> None:
    """Generate embedding vectors for one or more text inputs.

    Examples:
      orouter embed --input "hello world" --model openai/text-embedding-3-small
      orouter embed --input "doc one" --input "doc two" --model openai/text-embedding-3-small
      echo "piped text" | orouter embed --model openai/text-embedding-3-small
    """
    if input_:
        payload = input_ if len(input_) > 1 else input_[0]
    else:
        stdin_text = sys.stdin.read().strip()
        if not stdin_text:
            raise ValidationError(
                "No --input given and stdin is empty. Pass --input TEXT (repeatable) or pipe text in."
            )
        payload = stdin_text

    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)
    resolved_model = get_embedding_model(model)

    with sdk_adapter.build_adapter(api_key, get_base_url(run_ctx)) as adapter:
        result = adapter.embeddings_generate(
            model=resolved_model,
            input=payload,
            dimensions=dimensions,
            encoding_format=encoding_format,
            input_type=input_type,
        )

    def render(data):
        for i, vec in enumerate(data["embeddings"]):
            if isinstance(vec, str):
                echo(f"[{i}] (base64-encoded, {len(vec)} chars)")
            else:
                preview = ", ".join(f"{v:.4f}" for v in vec[:5])
                echo(f"[{i}] dim={len(vec)}  [{preview}, ...]")

    emit_result({"model": resolved_model, "embeddings": result.embeddings}, render)
