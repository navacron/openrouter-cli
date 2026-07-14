import typer

from openrouter_cli.config import get_api_key, get_base_url, get_run_ctx
from openrouter_cli.output import echo, emit_result, handle_errors
from openrouter_cli import sdk_adapter

app = typer.Typer(help="Look up metadata for past generations.", no_args_is_help=True)


@app.command("info")
@handle_errors
def info(
    generation_id: str = typer.Argument(
        ..., help="Generation id, e.g. from analyze/chat's raw JSON output's 'id' field."
    ),
) -> None:
    """Look up cost/usage metadata for a past chat, image, or video generation.

    Examples:
      orouter generation info gen-abc123
      orouter --json generation info gen-abc123
    """
    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)

    with sdk_adapter.build_adapter(api_key, get_base_url(run_ctx)) as adapter:
        data = adapter.get_generation(generation_id)

    def render(d):
        echo(f"{d.get('id', generation_id)}  model={d.get('model')}")
        if d.get("provider_name"):
            echo(f"  provider: {d['provider_name']}")
        if d.get("total_cost") is not None:
            echo(f"  cost: {d['total_cost']}")
        if d.get("tokens_prompt") is not None or d.get("tokens_completion") is not None:
            echo(f"  tokens: prompt={d.get('tokens_prompt')} completion={d.get('tokens_completion')}")
        if d.get("generation_time") is not None:
            echo(f"  generation time: {d['generation_time']}s")

    emit_result(data, render)
