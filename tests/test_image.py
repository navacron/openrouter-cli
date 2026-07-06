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


def test_image_edit_passes_input_references(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(image_result=ImageResult(images_b64=["YQ=="], media_types=[None], raw={}))
    _patch(monkeypatch, fake)
    ref = tmp_path / "photo.jpg"
    ref.write_bytes(b"fake")
    out = tmp_path / "edited.png"

    result = runner.invoke(
        app,
        [
            "image", "edit", "--input", str(ref), "--prompt", "make the sky sunset colored",
            "--output", str(out),
        ],
    )

    assert result.exit_code == 0, result.output
    assert out.read_bytes() == b"a"
    call = fake.calls[0]
    assert call[0] == "image_generate"
    refs = call[1]["input_references"]
    assert len(refs) == 1
    assert refs[0]["type"] == "image_url"
    assert refs[0]["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_image_edit_multiple_references_and_url_passthrough(runner, api_key_env, monkeypatch, tmp_path):
    fake = FakeAdapter(image_result=ImageResult(images_b64=["YQ=="], media_types=[None], raw={}))
    _patch(monkeypatch, fake)
    a = tmp_path / "a.png"
    a.write_bytes(b"fake")
    out = tmp_path / "combo.png"

    result = runner.invoke(
        app,
        [
            "image", "edit",
            "--input", str(a),
            "--input", "https://example.com/b.png",
            "--prompt", "blend these",
            "--output", str(out),
        ],
    )

    assert result.exit_code == 0, result.output
    refs = fake.calls[0][1]["input_references"]
    assert len(refs) == 2
    assert refs[0]["image_url"]["url"].startswith("data:image/png;base64,")
    assert refs[1]["image_url"]["url"] == "https://example.com/b.png"


def test_image_edit_missing_api_key(runner, monkeypatch, tmp_path):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    ref = tmp_path / "photo.jpg"
    ref.write_bytes(b"fake")
    out = tmp_path / "out.png"

    result = runner.invoke(
        app, ["image", "edit", "--input", str(ref), "--prompt", "x", "--output", str(out)]
    )

    assert result.exit_code == 2
    assert not out.exists()


def test_image_models_lists_ids(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(image_models=[{"id": "model/a"}, {"id": "model/b"}])
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["image", "models"])

    assert result.exit_code == 0, result.output
    assert "model/a" in result.output
    assert "model/b" in result.output
