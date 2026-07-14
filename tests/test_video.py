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


def test_video_generate_with_frame_image(runner, api_key_env, monkeypatch, tmp_path):
    job = VideoJob(job_id="abc123", status="pending", error=None, unsigned_urls=[], raw={})
    fake = FakeAdapter(video_job=job)
    _patch(monkeypatch, fake)
    frame = tmp_path / "first.png"
    frame.write_bytes(b"fake-png-bytes")

    result = runner.invoke(
        app,
        [
            "video", "generate", "--prompt", "the kite lifts off",
            "--frame-image", str(frame), "--frame-position", "first",
        ],
    )

    assert result.exit_code == 0, result.output
    call = fake.calls[0]
    assert call[0] == "video_generate"
    frames = call[1]["frame_images"]
    assert len(frames) == 1
    assert frames[0]["frame_type"] == "first_frame"
    assert frames[0]["type"] == "image_url"
    assert frames[0]["image_url"]["url"].startswith("data:image/png;base64,")


def test_video_generate_frame_image_position_mismatch(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(video_job=VideoJob(job_id="x", status="pending", error=None, unsigned_urls=[], raw={}))
    _patch(monkeypatch, fake)
    frame = tmp_path / "first.png"
    frame.write_bytes(b"fake")

    result = runner.invoke(
        app, ["video", "generate", "--prompt", "p", "--frame-image", str(frame)]
    )

    assert result.exit_code == 2
    assert not fake.calls


def test_video_generate_frame_position_invalid_value(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(video_job=VideoJob(job_id="x", status="pending", error=None, unsigned_urls=[], raw={}))
    _patch(monkeypatch, fake)
    frame = tmp_path / "first.png"
    frame.write_bytes(b"fake")

    result = runner.invoke(
        app,
        ["video", "generate", "--prompt", "p", "--frame-image", str(frame), "--frame-position", "middle"],
    )

    assert result.exit_code == 2
    assert not fake.calls


def test_video_wait_polls_and_downloads(runner, api_key_env, monkeypatch, tmp_path):
    sequence = [
        VideoJob(job_id="abc123", status="in_progress", error=None, unsigned_urls=[], raw={}),
        VideoJob(job_id="abc123", status="completed", error=None, unsigned_urls=["u"], raw={}),
    ]
    fake = FakeAdapter(video_status_sequence=sequence, video_content=b"mp4bytes")
    _patch(monkeypatch, fake)
    out = tmp_path / "paicha.mp4"

    result = runner.invoke(
        app, ["video", "wait", "abc123", "--output", str(out), "--poll-interval", "0"]
    )

    assert result.exit_code == 0, result.output
    assert out.read_bytes() == b"mp4bytes"
    statuses = [c for c in fake.calls if c[0] == "video_get_status"]
    assert len(statuses) == 2


def test_video_wait_timeout(runner, api_key_env, monkeypatch, tmp_path):
    sequence = [VideoJob(job_id="abc123", status="pending", error=None, unsigned_urls=[], raw={})] * 5
    fake = FakeAdapter(video_status_sequence=sequence)
    _patch(monkeypatch, fake)
    out = tmp_path / "paicha.mp4"

    result = runner.invoke(
        app,
        ["video", "wait", "abc123", "--output", str(out), "--poll-interval", "0", "--timeout", "0"],
    )

    assert result.exit_code == 3
    assert not out.exists()
