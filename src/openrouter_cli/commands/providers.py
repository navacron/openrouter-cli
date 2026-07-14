import typer

from openrouter_cli.config import get_api_key, get_base_url, get_run_ctx
from openrouter_cli.output import echo, emit_result, handle_errors
from openrouter_cli import sdk_adapter

app = typer.Typer(help="Discover model hosting providers.", no_args_is_help=True)


@app.command("list")
@handle_errors
def list_providers() -> None:
    """List model hosting providers available on OpenRouter.

    Examples:
      orouter providers list
      orouter --json providers list
    """
    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)

    with sdk_adapter.build_adapter(api_key, get_base_url(run_ctx)) as adapter:
        items = adapter.list_providers()

    def render(data):
        for p in data["providers"]:
            echo(f"{p.get('slug')}  {p.get('name', '')}")

    emit_result({"providers": items}, render)
