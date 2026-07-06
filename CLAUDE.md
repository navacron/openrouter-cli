# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup (editable install, dev extras)
source .venv/bin/activate          # venv already exists at repo root
pip install -e ".[dev]"

# Run the full test suite
pytest

# Run a single test file / single test
pytest tests/test_video.py
pytest tests/test_video.py::test_video_generate_wait_polls_and_downloads

# Run the CLI itself
orouter --help
orouter <command> --help           # every command's --help includes runnable examples
```

There is no configured linter, formatter, or type checker (no ruff/black/mypy config in
pyproject.toml) — don't assume one exists.

## Architecture

`orouter` is a Typer CLI wrapping the `openrouter` PyPI SDK (chat/vision, image generation,
video generation). The design is built around one hard rule: **`src/openrouter_cli/sdk_adapter.py`
is the only file that imports `openrouter`.** The SDK is Speakeasy-generated with easy-to-typo
attribute/kwarg/field names (`client.video_generation.get_generation(job_id=...)`, response fields
like `.b64_json`, `.unsigned_urls`, etc.) — isolating it behind one adapter means a future SDK
version bump only requires fixing this one file. `sdk_adapter.py` converts every SDK call into a
small dataclass (`ChatAnalysisResult`, `ImageResult`, `VideoJob`) so command code never touches
SDK pydantic objects directly. Before changing adapter internals, verify method/kwarg names by
inspecting the installed package directly (`python -c "import openrouter, inspect; ..."`) rather
than trusting memory or docs — the SDK is auto-generated and names don't always match intuition.

**Command modules import the module, not the function**: `commands/*.py` do
`from openrouter_cli import sdk_adapter` and call `sdk_adapter.build_adapter(...)`, never
`from openrouter_cli.sdk_adapter import build_adapter`. This is deliberate — it's the seam tests
monkeypatch (`monkeypatch.setattr(sdk_adapter, "build_adapter", ...)` in `tests/fakes.py`); a
direct-import binding would make the module attribute patch invisible to already-imported command
code. Keep this pattern when adding new commands.

**Run context is a module-level global, not Click's context object.** `config.py` holds
`RunContext` (json_mode/api_key/base_url) set once by `app.py`'s root Typer callback via
`config.set_run_ctx(...)` and read anywhere via `config.get_run_ctx()`. This exists because Typer
0.26 no longer depends on the standalone `click` package (it vendors its own fork under
`typer._click`), so the old `click.get_current_context().obj` pattern doesn't work — don't
reintroduce a `click` import.

**Every command is wrapped in `@handle_errors`** (`output.py`), which converts the `OrouterError`
hierarchy (`errors.py`: `ConfigError`/`ValidationError`=2, `ApiError`=1, `PollTimeoutError`=3,
`JobFailedError`=4) into either plain stderr text or, in `--json` mode, a
`{"error": {"type", "message", "details"}}` payload on stderr — with a matching process exit code
either way. Success output goes through `output.emit_result(data, human_renderer)`, which prints
`json.dumps(data)` to stdout in `--json` mode or calls the human renderer otherwise. New commands
should follow this pattern rather than printing directly, so agents can reliably parse output.

**Video generation is async** (submit → poll → download): `commands/video.py` + `polling.py`
implement the `--wait` loop (`poll_until_done`), which treats `completed` as success,
`failed`/`cancelled`/`expired` as `JobFailedError`, and elapsed-time-over-`--timeout` as
`PollTimeoutError` (the job keeps running server-side; the error message points at
`video status`/`video download` for later retrieval). Image generation is synchronous by
contrast — `commands/image.py` decodes and writes base64 output directly.

**Multimodal content-part construction** lives in `mime_utils.py`. Content-type is detected from
the file extension (or `--type` override), then `build_content_part()` builds the exact
OpenAI-compatible part for `analyze`: `image_url`/`video_url`/`file.file_data` all accept either a
plain URL or a base64 `data:` URI (confirmed against the SDK's component schema, so URLs pass
through untouched for images/video/PDF), but `input_audio` only accepts base64 with no URL field,
so audio is always downloaded and encoded first.

**`.env` loading requires `find_dotenv(usecwd=True)`**, not bare `load_dotenv()` — python-dotenv's
default file-finding uses stack-frame inspection, which resolves to the installed package's
location rather than the user's actual working directory once running from a console-script entry
point. This is set up once in `app.py:main()` before the Typer app runs.

Default model constants (`DEFAULT_CHAT_MODEL`, `DEFAULT_IMAGE_MODEL`, `DEFAULT_VIDEO_MODEL` in
`config.py`) are placeholders that may drift as OpenRouter's catalog changes — verify against
`orouter models list` / `orouter image models` / `orouter video models` before relying on them.

## Testing

Tests use Typer's `CliRunner` invoking the real `app` object in-process (no network, no
subprocess). The `tests/fakes.py::FakeAdapter` + `build_adapter_factory()` stand in for
`OpenRouterAdapter` — every test that needs adapter behavior monkeypatches
`openrouter_cli.sdk_adapter.build_adapter` to return a configured `FakeAdapter` (canned
results, or `raise_exc=` to simulate an SDK failure). The `_reset_run_ctx` autouse fixture in
`conftest.py` clears the module-level `RunContext` between tests.
