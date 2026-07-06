from pathlib import Path
from typing import Optional

import typer

from openrouter_cli import io_utils
from openrouter_cli.config import get_api_key, get_base_url, get_run_ctx, get_video_model
from openrouter_cli.errors import ValidationError
from openrouter_cli.output import echo, emit_result, handle_errors
from openrouter_cli.polling import poll_until_done
from openrouter_cli import sdk_adapter

app = typer.Typer(help="Generate, poll, and download videos.", no_args_is_help=True)


@app.command("generate")
@handle_errors
def generate(
    prompt: str = typer.Option(..., "--prompt", "-p", help="Text description of the desired video."),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Video model to use. Defaults to $OPENROUTER_VIDEO_MODEL."
    ),
    aspect_ratio: Optional[str] = typer.Option(None, "--aspect-ratio", help="e.g. 16:9, 9:16, 1:1."),
    duration: Optional[int] = typer.Option(None, "--duration", help="Video length in seconds."),
    resolution: Optional[str] = typer.Option(None, "--resolution", help="e.g. 720p, 1080p, 4K."),
    seed: Optional[int] = typer.Option(None, "--seed"),
    generate_audio: Optional[bool] = typer.Option(None, "--audio/--no-audio"),
    size: Optional[str] = typer.Option(None, "--size"),
    wait: bool = typer.Option(False, "--wait", help="Poll until the job finishes and download it."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Required with --wait."),
    poll_interval: float = typer.Option(5.0, "--poll-interval", help="Seconds between status checks."),
    timeout: float = typer.Option(600.0, "--timeout", help="Give up waiting after this many seconds."),
) -> None:
    """Generate a video from a text prompt. Video generation is asynchronous.

    Examples:
      orouter video generate --prompt "Two Pakistani kites fighting" --model google/veo-3.1 --wait --output paicha.mp4
      orouter video generate --prompt "a golden retriever playing fetch"
      orouter video status <job_id>
      orouter video download <job_id> --output paicha.mp4
    """
    if wait and output is None:
        raise ValidationError("--wait requires --output <file> so the finished video can be saved.")

    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)
    resolved_model = get_video_model(model)

    with sdk_adapter.build_adapter(api_key, get_base_url(run_ctx)) as adapter:
        job = adapter.video_generate(
            model=resolved_model,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            duration=duration,
            resolution=resolution,
            seed=seed,
            generate_audio=generate_audio,
            size=size,
        )

        if not wait:
            def render_no_wait(data):
                echo(f"Submitted video job {data['job_id']} (status: {data['status']}).")
                echo(f"Check it with: orouter video status {data['job_id']}")
                echo(f"Download it with: orouter video download {data['job_id']} --output <file>")

            emit_result({"job_id": job.job_id, "status": job.status}, render_no_wait)
            return

        def on_tick(j):
            echo(f"job {j.job_id}: {j.status}")

        finished = poll_until_done(
            adapter, job.job_id, poll_interval=poll_interval, timeout=timeout, on_tick=on_tick
        )
        data = adapter.video_download(finished.job_id)
        io_utils.write_bytes(output, data)

        def render(result):
            echo(f"Saved {result['file']}")

        emit_result(
            {"job_id": finished.job_id, "status": finished.status, "file": str(output)}, render
        )


@app.command("status")
@handle_errors
def status(job_id: str = typer.Argument(..., help="Job id returned by `video generate`.")) -> None:
    """Check the status of a video generation job.

    Examples:
      orouter video status abc123
    """
    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)

    with sdk_adapter.build_adapter(api_key, get_base_url(run_ctx)) as adapter:
        job = adapter.video_get_status(job_id)

    def render(data):
        echo(f"{data['job_id']}: {data['status']}")
        if data.get("error"):
            echo(f"  error: {data['error']}")

    emit_result(
        {"job_id": job.job_id, "status": job.status, "error": job.error}, render
    )


@app.command("download")
@handle_errors
def download(
    job_id: str = typer.Argument(..., help="Job id returned by `video generate`."),
    output: Path = typer.Option(..., "--output", "-o"),
    index: int = typer.Option(0, "--index", help="Which generated variant to download, if more than one."),
) -> None:
    """Download a completed video generation job's content.

    Examples:
      orouter video download abc123 --output paicha.mp4
    """
    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)

    with sdk_adapter.build_adapter(api_key, get_base_url(run_ctx)) as adapter:
        data = adapter.video_download(job_id, index=index)

    io_utils.write_bytes(output, data)

    def render(result):
        echo(f"Saved {result['file']}")

    emit_result({"job_id": job_id, "file": str(output)}, render)


@app.command("models")
@handle_errors
def models() -> None:
    """List available video generation models.

    Examples:
      orouter video models
      orouter --json video models
    """
    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)

    with sdk_adapter.build_adapter(api_key, get_base_url(run_ctx)) as adapter:
        items = adapter.list_video_models()

    def render(data):
        for m in data["models"]:
            echo(m.get("id", m))

    emit_result({"models": items}, render)
