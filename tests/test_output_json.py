import json

from openrouter_cli.app import app


def test_json_error_is_valid_json_and_human_mode_is_not(runner, monkeypatch, tmp_path):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    img = tmp_path / "a.jpg"
    img.write_bytes(b"fake")

    json_result = runner.invoke(app, ["--json", "analyze", str(img), "--prompt", "hi"])
    payload = json.loads(json_result.output)
    assert "error" in payload
    assert payload["error"]["type"] == "ConfigError"

    text_result = runner.invoke(app, ["analyze", str(img), "--prompt", "hi"])
    try:
        json.loads(text_result.output)
        is_json = True
    except json.JSONDecodeError:
        is_json = False
    assert not is_json
