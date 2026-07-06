# openrouter-cli

`orouter` is a command-line interface for [OpenRouter](https://openrouter.ai): chat, analyze
multimodal files, generate images/video/speech, transcribe audio, and discover models - from the
shell or from a coding agent like Claude Code.

## Install

```bash
python3 -m venv .venv          # optional, but recommended
source .venv/bin/activate
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

Every command supports `--json` for machine-readable output (stdout is pure JSON, errors become
JSON on stderr too), and every command's `--help` includes runnable examples - run
`orouter --help` or `orouter <command> --help` to explore the full surface.

### Chat

```bash
# Plain text chat, no file
orouter chat "What is the capital of France?"

# Analyze any multimodal file (image, video, audio, or PDF - auto-detected)
orouter analyze kite.mp4 --prompt "Analyze flight physics" --model google/gemini-3-pro
```

### Image

```bash
# Generate an image
orouter image generate --prompt "Traditional Lahore patang" --output patang.png

# Generate an image with a specific model
orouter image generate --prompt "Traditional Lahore patang" --model google/gemini-3.1-flash-lite-image --output patang.png

# Edit or combine reference image(s) with a text prompt
orouter image edit --input patang.png --prompt "make the sky sunset colored" --output edited.png

# Discover available image models
orouter image models
```

### Video

```bash
# Generate a video (asynchronous - --wait polls until it's done and downloads it)
orouter video generate --prompt "Two Pakistani kites fighting" --model google/veo-3.1 --wait --output paicha.mp4

# Generate a video with audio using a specific model
orouter video generate --prompt "Kids flying kites on a rooftop in Old Lahore, Pakistan" --model bytedance/seedance-2.0 --audio --wait --output lahore_kites.mp4

# Check on a job submitted without --wait, then download it once complete
orouter video status <job_id>
orouter video download <job_id> --output paicha.mp4

# Discover available video models
orouter video models
```

### Audio

```bash
# Transcribe a local or remote audio file to text
orouter audio transcribe voice_note.mp3 --model openai/whisper-1

# Synthesize speech from text
orouter audio speak "Hello from Lahore" --voice alloy --model openai/tts-1 --output hello.mp3
```

### Models

```bash
# Discover chat/vision models before picking --model
orouter models list --input-modality video
orouter models list --query gemini
```

### Account

```bash
# Check your OpenRouter credit balance
orouter credits
```

### Environment variables

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | required |
| `OPENROUTER_MODEL` | default model for `analyze` / `chat` |
| `OPENROUTER_IMAGE_MODEL` | default model for `image generate` / `image edit` |
| `OPENROUTER_VIDEO_MODEL` | default model for `video generate` |
| `OPENROUTER_STT_MODEL` | default model for `audio transcribe` (no built-in default) |
| `OPENROUTER_TTS_MODEL` | default model for `audio speak` (no built-in default) |
| `OPENROUTER_BASE_URL` | advanced: override the API base URL |

## Development

```bash
pip install -e ".[dev]"
pytest                                    # full suite
pytest tests/test_video.py                # single file
pytest tests/test_video.py::test_video_generate_wait_polls_and_downloads  # single test
```

See `CLAUDE.md` for an architecture overview (SDK isolation boundary, output/error
conventions, testing seam) if you're working on the codebase itself.
