from openrouter_cli.config import get_api_key, get_base_url, get_run_ctx
from openrouter_cli.output import echo, emit_result, handle_errors
from openrouter_cli import sdk_adapter


@handle_errors
def credits() -> None:
    """Show OpenRouter account credit balance (total purchased, used, and remaining).

    Examples:
      orouter credits
      orouter --json credits
    """
    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)

    with sdk_adapter.build_adapter(api_key, get_base_url(run_ctx)) as adapter:
        info = adapter.get_credits()

    def render(data):
        echo(f"Total credits: {data['total_credits']}")
        echo(f"Total usage:   {data['total_usage']}")
        echo(f"Balance:       {data['balance']}")

    emit_result(
        {"total_credits": info.total_credits, "total_usage": info.total_usage, "balance": info.balance},
        render,
    )
