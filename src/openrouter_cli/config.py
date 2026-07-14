import dataclasses
import os
from typing import Optional

from openrouter_cli.errors import ConfigError

# openrouter/auto is OpenRouter's own auto-router model: always available, a safe
# default for text analysis. Image/video defaults are placeholders - list current
# options with `orouter image models` / `orouter video models` and override with
# --model or the env vars below.
DEFAULT_CHAT_MODEL = "openrouter/auto"
DEFAULT_IMAGE_MODEL = "google/gemini-2.5-flash-image"
DEFAULT_VIDEO_MODEL = "google/veo-3.1"


@dataclasses.dataclass
class RunContext:
    json_mode: bool
    api_key: Optional[str]
    base_url: Optional[str]


_run_ctx: Optional[RunContext] = None


def set_run_ctx(run_ctx: RunContext) -> None:
    """Set once by the root Typer callback at process startup."""
    global _run_ctx
    _run_ctx = run_ctx


def get_run_ctx() -> RunContext:
    assert _run_ctx is not None, "RunContext accessed before the root CLI callback ran"
    return _run_ctx


def get_api_key(run_ctx: RunContext) -> str:
    key = run_ctx.api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ConfigError(
            "OPENROUTER_API_KEY is not set. Export it, put it in a .env file, or "
            "pass --api-key before running this command. Create a key at "
            "https://openrouter.ai/keys"
        )
    return key


def get_base_url(run_ctx: RunContext) -> Optional[str]:
    return run_ctx.base_url or os.environ.get("OPENROUTER_BASE_URL")


def get_chat_model(explicit: Optional[str]) -> str:
    return explicit or os.environ.get("OPENROUTER_MODEL") or DEFAULT_CHAT_MODEL


def get_image_model(explicit: Optional[str]) -> str:
    return explicit or os.environ.get("OPENROUTER_IMAGE_MODEL") or DEFAULT_IMAGE_MODEL


def get_video_model(explicit: Optional[str]) -> str:
    return explicit or os.environ.get("OPENROUTER_VIDEO_MODEL") or DEFAULT_VIDEO_MODEL


# No DEFAULT_STT_MODEL/DEFAULT_TTS_MODEL: unlike chat/image/video, there's no SDK
# list_models() endpoint for these modalities to sanity-check a guessed default
# against, so require the caller to be explicit instead of silently picking one.


def get_stt_model(explicit: Optional[str]) -> str:
    model = explicit or os.environ.get("OPENROUTER_STT_MODEL")
    if not model:
        raise ConfigError(
            "No speech-to-text model specified. Pass --model or set $OPENROUTER_STT_MODEL. "
            "Discover options with `orouter models list --input-modality audio`."
        )
    return model


def get_tts_model(explicit: Optional[str]) -> str:
    model = explicit or os.environ.get("OPENROUTER_TTS_MODEL")
    if not model:
        raise ConfigError(
            "No text-to-speech model specified. Pass --model or set $OPENROUTER_TTS_MODEL. "
            "Discover options with `orouter models list --output-modality audio`."
        )
    return model


def get_embedding_model(explicit: Optional[str]) -> str:
    model = explicit or os.environ.get("OPENROUTER_EMBEDDING_MODEL")
    if not model:
        raise ConfigError(
            "No embedding model specified. Pass --model or set $OPENROUTER_EMBEDDING_MODEL. "
            "Discover options with `orouter models list --output-modality embeddings`."
        )
    return model


def get_rerank_model(explicit: Optional[str]) -> str:
    model = explicit or os.environ.get("OPENROUTER_RERANK_MODEL")
    if not model:
        raise ConfigError(
            "No rerank model specified. Pass --model or set $OPENROUTER_RERANK_MODEL."
        )
    return model
