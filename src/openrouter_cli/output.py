import functools
import json
from typing import Any, Callable

import typer

from openrouter_cli.config import get_run_ctx
from openrouter_cli.errors import ApiError, OrouterError


def emit_result(data: dict[str, Any], human_renderer: Callable[[dict[str, Any]], None]) -> None:
    run_ctx = get_run_ctx()
    if run_ctx.json_mode:
        typer.echo(json.dumps(data, indent=2))
    else:
        human_renderer(data)


def emit_error(exc: OrouterError) -> None:
    run_ctx = get_run_ctx()
    if run_ctx.json_mode:
        payload = {
            "error": {
                "type": type(exc).__name__,
                "message": exc.message,
                "details": exc.details,
            }
        }
        typer.echo(json.dumps(payload, indent=2), err=True)
    else:
        typer.secho(f"Error: {exc.message}", fg=typer.colors.RED, err=True)
        for key, value in exc.details.items():
            typer.secho(f"  {key}: {value}", fg=typer.colors.RED, err=True)


def handle_errors(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OrouterError as e:
            emit_error(e)
            raise typer.Exit(code=e.exit_code)
        except typer.Exit:
            raise
        except Exception as e:  # noqa: BLE001 - last-resort safety net for agents
            emit_error(ApiError(str(e), details={"exception_type": type(e).__name__}))
            raise typer.Exit(code=1)

    return wrapper


def echo(*args, **kwargs) -> None:
    """Human-mode-only echo; no-op when --json is set (keeps stdout pure JSON)."""
    run_ctx = get_run_ctx()
    if not run_ctx.json_mode:
        typer.echo(*args, **kwargs)


def echo_err(*args, **kwargs) -> None:
    kwargs.setdefault("err", True)
    typer.echo(*args, **kwargs)
