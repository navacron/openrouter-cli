import json

from openrouter_cli import sdk_adapter
from openrouter_cli.app import app
from openrouter_cli.sdk_adapter import ImageResult
from tests.fakes import FakeAdapter, build_adapter_factory


def _patch(monkeypatch, fake: FakeAdapter):
    monkeypatch.setattr(sdk_adapter, "build_adapter", build_adapter_factory(fake))


def test_image_generate_writes_output_file(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(image_result=ImageResult(images_b64=["ZmFrZXBuZw=="], media_types=[None], raw={}))
    _patch(monkeypatch, fake)
    out = tmp_path / "patang.png"

    result = runner.invoke(
        app, ["image", "generate", "--prompt", "Traditional Lahore patang", "--output", str(out)]
    )

    assert result.exit_code == 0, result.output
    assert out.read_bytes() == b"fakepng"


def test_image_generate_multiple_images_numbered(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(
        image_result=ImageResult(images_b64=["YQ==", "Yg==", "Yw=="], media_types=[None, None, None], raw={})
    )
    _patch(monkeypatch, fake)
    out = tmp_path / "logo.png"

    result = runner.invoke(app, ["image", "generate", "--prompt", "logos", "--n", "3", "--output", str(out)])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "logo.png").read_bytes() == b"a"
    assert (tmp_path / "logo_2.png").read_bytes() == b"b"
    assert (tmp_path / "logo_3.png").read_bytes() == b"c"


def test_image_generate_missing_api_key(runner, monkeypatch, tmp_path):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    out = tmp_path / "x.png"

    result = runner.invoke(app, ["image", "generate", "--prompt", "x", "--output", str(out)])

    assert result.exit_code == 2
    assert not out.exists()


def test_image_generate_json_output(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(image_result=ImageResult(images_b64=["YQ=="], media_types=[None], raw={}))
    _patch(monkeypatch, fake)
    out = tmp_path / "a.png"

    result = runner.invoke(app, ["--json", "image", "generate", "--prompt", "x", "--output", str(out)])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["files"] == [str(out)]


def test_image_models_lists_ids(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(image_models=[{"id": "model/a"}, {"id": "model/b"}])
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["image", "models"])

    assert result.exit_code == 0, result.output
    assert "model/a" in result.output
    assert "model/b" in result.output
