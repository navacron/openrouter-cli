import json

from openrouter_cli import sdk_adapter
from openrouter_cli.app import app
from openrouter_cli.sdk_adapter import VideoJob
from tests.fakes import FakeAdapter, build_adapter_factory


def _patch(monkeypatch, fake: FakeAdapter):
    monkeypatch.setattr(sdk_adapter, "build_adapter", build_adapter_factory(fake))


def test_video_generate_without_wait_returns_job_immediately(runner, api_key_env, monkeypatch):
    job = VideoJob(job_id="abc123", status="pending", error=None, unsigned_urls=[], raw={})
    fake = FakeAdapter(video_job=job)
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["video", "generate", "--prompt", "kites fighting"])

    assert result.exit_code == 0, result.output
    assert "abc123" in result.output
    assert not any(name == "video_get_status" for name, _ in fake.calls)


def test_video_generate_wait_requires_output(runner, api_key_env, monkeypatch):
    job = VideoJob(job_id="abc123", status="pending", error=None, unsigned_urls=[], raw={})
    fake = FakeAdapter(video_job=job)
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["video", "generate", "--prompt", "kites fighting", "--wait"])

    assert result.exit_code == 2
    assert "--output" in result.output


def test_video_generate_wait_polls_and_downloads(runner, api_key_env, monkeypatch, tmp_path):
    submitted = VideoJob(job_id="abc123", status="pending", error=None, unsigned_urls=[], raw={})
    sequence = [
        VideoJob(job_id="abc123", status="pending", error=None, unsigned_urls=[], raw={}),
        VideoJob(job_id="abc123", status="in_progress", error=None, unsigned_urls=[], raw={}),
        VideoJob(job_id="abc123", status="completed", error=None, unsigned_urls=["u"], raw={}),
    ]
    fake = FakeAdapter(video_job=submitted, video_status_sequence=sequence, video_content=b"mp4bytes")
    _patch(monkeypatch, fake)
    out = tmp_path / "paicha.mp4"

    result = runner.invoke(
        app,
        [
            "video", "generate", "--prompt", "kites fighting", "--wait", "--output", str(out),
            "--poll-interval", "0",
        ],
    )

    assert result.exit_code == 0, result.output
    assert out.read_bytes() == b"mp4bytes"
    statuses = [c for c in fake.calls if c[0] == "video_get_status"]
    assert len(statuses) == 3


def test_video_generate_wait_timeout(runner, api_key_env, monkeypatch, tmp_path):
    submitted = VideoJob(job_id="abc123", status="pending", error=None, unsigned_urls=[], raw={})
    sequence = [VideoJob(job_id="abc123", status="pending", error=None, unsigned_urls=[], raw={})] * 5
    fake = FakeAdapter(video_job=submitted, video_status_sequence=sequence)
    _patch(monkeypatch, fake)
    out = tmp_path / "paicha.mp4"

    result = runner.invoke(
        app,
        [
            "video", "generate", "--prompt", "kites fighting", "--wait", "--output", str(out),
            "--poll-interval", "0", "--timeout", "0",
        ],
    )

    assert result.exit_code == 3
    assert not out.exists()


def test_video_generate_wait_job_failed(runner, api_key_env, monkeypatch, tmp_path):
    submitted = VideoJob(job_id="abc123", status="pending", error=None, unsigned_urls=[], raw={})
    sequence = [VideoJob(job_id="abc123", status="failed", error="provider error", unsigned_urls=[], raw={})]
    fake = FakeAdapter(video_job=submitted, video_status_sequence=sequence)
    _patch(monkeypatch, fake)
    out = tmp_path / "paicha.mp4"

    result = runner.invoke(
        app,
        ["video", "generate", "--prompt", "kites fighting", "--wait", "--output", str(out), "--poll-interval", "0"],
    )

    assert result.exit_code == 4
    assert not out.exists()


def test_video_status(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(video_job=VideoJob(job_id="abc123", status="in_progress", error=None, unsigned_urls=[], raw={}))
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["video", "status", "abc123"])

    assert result.exit_code == 0, result.output
    assert "in_progress" in result.output


def test_video_download(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(video_content=b"videodata")
    _patch(monkeypatch, fake)
    out = tmp_path / "out.mp4"

    result = runner.invoke(app, ["video", "download", "abc123", "--output", str(out)])

    assert result.exit_code == 0, result.output
    assert out.read_bytes() == b"videodata"


def test_video_models(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(video_models=[{"id": "google/veo-3.1"}])
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["video", "models"])

    assert result.exit_code == 0, result.output
    assert "google/veo-3.1" in result.output


def test_video_generate_json_no_wait(runner, api_key_env, monkeypatch):
    job = VideoJob(job_id="abc123", status="pending", error=None, unsigned_urls=[], raw={})
    fake = FakeAdapter(video_job=job)
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["--json", "video", "generate", "--prompt", "kites"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload == {"job_id": "abc123", "status": "pending"}
