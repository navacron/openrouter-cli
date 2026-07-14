from typing import Optional

import typer
from dotenv import find_dotenv, load_dotenv

from openrouter_cli import __version__
from openrouter_cli.commands import (
    analyze,
    audio,
    chat,
    credits,
    embed,
    generation,
    image,
    models,
    providers,
    rerank,
    video,
)
from openrouter_cli.config import RunContext, set_run_ctx

app = typer.Typer(
    name="orouter",
    help=(
        "OpenRouter CLI: analyze multimodal files, generate images and video, "
        "and discover models - built to be self-explanatory via --help for both "
        "humans and coding agents.\n\n"
        "Requires OPENROUTER_API_KEY, settable in the environment or in a .env file "
        "(searched upward from the current directory). Optional env vars: "
        "OPENROUTER_MODEL, OPENROUTER_IMAGE_MODEL, OPENROUTER_VIDEO_MODEL, "
        "OPENROUTER_BASE_URL. Run `orouter <command> --help` for detailed options "
        "and examples."
    ),
    add_completion=True,
    no_args_is_help=True,
)
app.add_typer(image.app, name="image")
app.add_typer(video.app, name="video")
app.add_typer(models.app, name="models")
app.add_typer(audio.app, name="audio")
app.add_typer(providers.app, name="providers")
app.add_typer(generation.app, name="generation")
app.command("analyze")(analyze.analyze)
app.command("chat")(chat.chat)
app.command("credits")(credits.credits)
app.command("embed")(embed.embed)
app.command("rerank")(rerank.rerank)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main_callback(
    json_: bool = typer.Option(
        False, "--json", help="Emit machine-readable JSON to stdout; errors become JSON on stderr too."
    ),
    api_key: Optional[str] = typer.Option(
        None, "--api-key", envvar="OPENROUTER_API_KEY", help="Overrides $OPENROUTER_API_KEY."
    ),
    base_url: Optional[str] = typer.Option(
        None, "--base-url", envvar="OPENROUTER_BASE_URL", help="Advanced: override the API base URL."
    ),
    version: Optional[bool] = typer.Option(
        None, "--version", callback=_version_callback, is_eager=True, help="Print the CLI version and exit."
    ),
) -> None:
    set_run_ctx(RunContext(json_mode=json_, api_key=api_key, base_url=base_url))


def main() -> None:
    # usecwd=True: search upward from the process's actual cwd, not from this
    # installed package's location (dotenv's default stack-inspection heuristic
    # picks the wrong directory once this runs from an installed console script).
    # Fills gaps in os.environ; real environment variables that are already set
    # always win.
    load_dotenv(find_dotenv(usecwd=True))
    app()


if __name__ == "__main__":
    main()
