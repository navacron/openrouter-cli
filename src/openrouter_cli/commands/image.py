from pathlib import Path
from typing import Optional

import typer

from openrouter_cli import io_utils
from openrouter_cli.config import get_api_key, get_base_url, get_image_model, get_run_ctx
from openrouter_cli.output import echo, emit_result, handle_errors
from openrouter_cli import sdk_adapter

app = typer.Typer(help="Generate images and discover image models.", no_args_is_help=True)


@app.command("generate")
@handle_errors
def generate(
    prompt: str = typer.Option(..., "--prompt", "-p", help="Text description of the desired image."),
    output: Path = typer.Option(..., "--output", "-o", help="Where to save the generated image."),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Image model to use. Defaults to $OPENROUTER_IMAGE_MODEL."
    ),
    n: int = typer.Option(1, "--n", help="Number of images to generate."),
    size: Optional[str] = typer.Option(None, "--size"),
    aspect_ratio: Optional[str] = typer.Option(None, "--aspect-ratio", help="e.g. 1:1, 16:9, 9:16."),
    resolution: Optional[str] = typer.Option(None, "--resolution", help="e.g. 1K, 2K, 4K."),
    quality: Optional[str] = typer.Option(None, "--quality", help="auto, low, medium, or high."),
    seed: Optional[int] = typer.Option(None, "--seed"),
    output_format: Optional[str] = typer.Option(None, "--output-format", help="png, jpeg, webp, or svg."),
) -> None:
    """Generate one or more images from a text prompt.

    Examples:
      orouter image generate --prompt "Traditional Lahore patang" --output patang.png
      orouter image generate --prompt "logo variations" --n 4 --output logo.png
    """
    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)
    resolved_model = get_image_model(model)

    with sdk_adapter.build_adapter(api_key, get_base_url(run_ctx)) as adapter:
        result = adapter.image_generate(
            model=resolved_model,
            prompt=prompt,
            n=n,
            size=size,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            quality=quality,
            seed=seed,
            output_format=output_format,
        )

    paths = io_utils.save_b64_images(result.images_b64, output)

    def render(data):
        for p in data["files"]:
            echo(p)

    emit_result(
        {"model": resolved_model, "prompt": prompt, "files": [str(p) for p in paths]},
        render,
    )


@app.command("models")
@handle_errors
def models() -> None:
    """List available image generation models.

    Examples:
      orouter image models
      orouter --json image models
    """
    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)

    with sdk_adapter.build_adapter(api_key, get_base_url(run_ctx)) as adapter:
        items = adapter.list_image_models()

    def render(data):
        for m in data["models"]:
            echo(m.get("id", m))

    emit_result({"models": items}, render)
