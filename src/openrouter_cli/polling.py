import time
from typing import Callable

from openrouter_cli.errors import JobFailedError, PollTimeoutError
from openrouter_cli.sdk_adapter import (
    TERMINAL_FAILURE_STATUSES,
    TERMINAL_SUCCESS_STATUSES,
    OpenRouterAdapter,
    VideoJob,
)


def poll_until_done(
    adapter: OpenRouterAdapter,
    job_id: str,
    *,
    poll_interval: float,
    timeout: float,
    on_tick: Callable[[VideoJob], None] = lambda job: None,
) -> VideoJob:
    start = time.monotonic()
    while True:
        job = adapter.video_get_status(job_id)
        on_tick(job)

        if job.status in TERMINAL_SUCCESS_STATUSES:
            return job

        if job.status in TERMINAL_FAILURE_STATUSES:
            raise JobFailedError(
                f"Video job {job_id} ended with status {job.status!r}: "
                f"{job.error or 'no error message provided'}",
                details={"job_id": job_id, "status": job.status},
            )

        if time.monotonic() - start >= timeout:
            raise PollTimeoutError(
                f"Timed out after {timeout}s waiting for video job {job_id} "
                f"(last status: {job.status!r}). The job keeps running server-side - "
                f"check it later with `orouter video status {job_id}` and download with "
                f"`orouter video download {job_id} --output <file>`.",
                details={"job_id": job_id, "status": job.status},
            )

        time.sleep(poll_interval)
