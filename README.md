# openrouter-cli

`orouter` is a command-line interface for [OpenRouter](https://openrouter.ai): analyze multimodal
files, generate images and video, and discover models - from the shell or from a coding agent
like Claude Code.

## Install

```bash
pip install -e .
export OPENROUTER_API_KEY=sk-or-...   # https://openrouter.ai/keys
```

Alternatively, copy `.env.example` to `.env` and fill in your key - `orouter` loads it
automatically (searching upward from the current directory). Real environment variables
always take precedence over `.env`.

```bash
cp .env.example .env
# edit .env and set OPENROUTER_API_KEY=...
```

## Usage

```bash
# Analyze any multimodal file (image, video, audio, or PDF - auto-detected)
orouter analyze kite.mp4 --prompt "Analyze flight physics" --model google/gemini-3-pro

# Generate an image
orouter image generate --prompt "Traditional Lahore patang" --output patang.png

# Generate a video (asynchronous - --wait polls until it's done and downloads it)
orouter video generate --prompt "Two Pakistani kites fighting" --model google/veo-3.1 --wait --output paicha.mp4

# Discover models before picking --model
orouter models list --input-modality video
orouter image models
orouter video models
```

Every command supports `--json` for machine-readable output (stdout is pure JSON, errors become
JSON on stderr too), and every command's `--help` includes runnable examples - run
`orouter --help` or `orouter <command> --help` to explore the full surface.

### Environment variables

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | required |
| `OPENROUTER_MODEL` | default model for `analyze` |
| `OPENROUTER_IMAGE_MODEL` | default model for `image generate` |
| `OPENROUTER_VIDEO_MODEL` | default model for `video generate` |
| `OPENROUTER_BASE_URL` | advanced: override the API base URL |

## Development

```bash
pip install -e ".[dev]"
pytest
```
