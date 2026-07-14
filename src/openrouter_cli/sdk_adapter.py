"""The only module that imports the `openrouter` SDK package.

Keeping every SDK call behind this adapter means a naming surprise in a new
SDK version only requires fixing this one file - command/CLI code only ever
sees the small dataclasses defined below.
"""

import dataclasses
from typing import Any, Optional

from openrouter import OpenRouter
from openrouter.errors import OpenRouterError

from openrouter_cli.errors import ApiError

TERMINAL_FAILURE_STATUSES = {"failed", "cancelled", "expired"}
TERMINAL_SUCCESS_STATUSES = {"completed"}


@dataclasses.dataclass
class ChatAnalysisResult:
    text: str
    model: str
    raw: dict[str, Any]


@dataclasses.dataclass
class ImageResult:
    images_b64: list[str]
    media_types: list[Optional[str]]
    raw: dict[str, Any]


@dataclasses.dataclass
class VideoJob:
    job_id: str
    status: str
    error: Optional[str]
    unsigned_urls: list[str]
    raw: dict[str, Any]


@dataclasses.dataclass
class TranscriptionResult:
    text: str
    raw: dict[str, Any]


@dataclasses.dataclass
class CreditsInfo:
    total_credits: float
    total_usage: float
    balance: float
    raw: dict[str, Any]


def _model_dump(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    return obj


def _extract_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            text = getattr(part, "text", None)
            if text is not None:
                parts.append(text)
        return "".join(parts)
    return str(content)


def _video_job_from_response(resp: Any) -> VideoJob:
    return VideoJob(
        job_id=resp.id,
        status=resp.status,
        error=getattr(resp, "error", None),
        unsigned_urls=list(getattr(resp, "unsigned_urls", None) or []),
        raw=_model_dump(resp),
    )


DEFAULT_TIMEOUT_MS = 120_000


class OpenRouterAdapter:
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        # The SDK's underlying httpx.Client is built with no explicit timeout,
        # so it falls back to httpx's 5s default. Slow endpoints (image/video
        # generation) blow past that, and a bare ReadTimeout is treated as a
        # retryable connection error - the SDK then silently retries with
        # exponential backoff for up to an hour (RetryConfig default
        # max_elapsed_time=3600000ms) before finally raising. Setting
        # timeout_ms here avoids the spurious timeouts that trigger it.
        kwargs: dict[str, Any] = {"api_key": api_key, "timeout_ms": DEFAULT_TIMEOUT_MS}
        if base_url:
            kwargs["server_url"] = base_url
        self._client = OpenRouter(**kwargs)

    def __enter__(self) -> "OpenRouterAdapter":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def close(self) -> None:
        close = getattr(self._client, "close", None)
        if callable(close):
            close()

    def _call(self, op: str, fn, **kwargs) -> Any:
        try:
            return fn(**kwargs)
        except OpenRouterError as e:
            raise ApiError(f"{op} failed: {e}") from e
        except Exception as e:  # noqa: BLE001
            raise ApiError(f"{op} failed: {e}") from e

    # -- chat / analyze -----------------------------------------------------

    def chat_send(
        self,
        *,
        model: str,
        content_parts: list[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ChatAnalysisResult:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": content_parts}],
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        result = self._call("chat.send", self._client.chat.send, **kwargs)
        text = _extract_text(result.choices[0].message.content)
        return ChatAnalysisResult(text=text, model=result.model, raw=_model_dump(result))

    def list_chat_models(
        self,
        *,
        input_modalities: Optional[str] = None,
        output_modalities: Optional[str] = None,
        q: Optional[str] = None,
    ) -> list[dict]:
        kwargs: dict[str, Any] = {}
        if input_modalities:
            kwargs["input_modalities"] = input_modalities
        if output_modalities:
            kwargs["output_modalities"] = output_modalities
        if q:
            kwargs["q"] = q
        result = self._call("models.list", self._client.models.list, **kwargs)
        return [_model_dump(m) for m in result.data]

    # -- images ---------------------------------------------------------------

    def image_generate(
        self,
        *,
        model: str,
        prompt: str,
        n: Optional[int] = None,
        size: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        quality: Optional[str] = None,
        seed: Optional[int] = None,
        output_format: Optional[str] = None,
        input_references: Optional[list[dict]] = None,
    ) -> ImageResult:
        kwargs: dict[str, Any] = {"model": model, "prompt": prompt}
        for k, v in dict(
            n=n,
            size=size,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            quality=quality,
            seed=seed,
            output_format=output_format,
            input_references=input_references,
        ).items():
            if v is not None:
                kwargs[k] = v
        result = self._call("images.generate", self._client.images.generate, **kwargs)
        return ImageResult(
            images_b64=[d.b64_json for d in result.data],
            media_types=[getattr(d, "media_type", None) for d in result.data],
            raw=_model_dump(result),
        )

    def list_image_models(self) -> list[dict]:
        result = self._call("images.list_models", self._client.images.list_models)
        return [_model_dump(m) for m in result.data]

    # -- video ------------------------------------------------------------------

    def video_generate(
        self,
        *,
        model: str,
        prompt: str,
        aspect_ratio: Optional[str] = None,
        duration: Optional[int] = None,
        resolution: Optional[str] = None,
        seed: Optional[int] = None,
        generate_audio: Optional[bool] = None,
        size: Optional[str] = None,
    ) -> VideoJob:
        kwargs: dict[str, Any] = {"model": model, "prompt": prompt}
        for k, v in dict(
            aspect_ratio=aspect_ratio,
            duration=duration,
            resolution=resolution,
            seed=seed,
            generate_audio=generate_audio,
            size=size,
        ).items():
            if v is not None:
                kwargs[k] = v
        result = self._call("video_generation.generate", self._client.video_generation.generate, **kwargs)
        return _video_job_from_response(result)

    def video_get_status(self, job_id: str) -> VideoJob:
        result = self._call(
            "video_generation.get_generation",
            self._client.video_generation.get_generation,
            job_id=job_id,
        )
        return _video_job_from_response(result)

    def video_download(self, job_id: str, index: int = 0) -> bytes:
        resp = self._call(
            "video_generation.get_video_content",
            self._client.video_generation.get_video_content,
            job_id=job_id,
            index=index,
        )
        # get_video_content returns a streamed httpx.Response - .content raises
        # ResponseNotRead until the body has actually been pulled off the wire.
        return resp.read()

    def list_video_models(self) -> list[dict]:
        result = self._call(
            "video_generation.list_videos_models", self._client.video_generation.list_videos_models
        )
        return [_model_dump(m) for m in result.data]

    # -- audio ------------------------------------------------------------------

    def audio_transcribe(
        self,
        *,
        model: str,
        input_audio: dict,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        kwargs: dict[str, Any] = {"model": model, "input_audio": input_audio}
        if language is not None:
            kwargs["language"] = language
        result = self._call("stt.create_transcription", self._client.stt.create_transcription, **kwargs)
        return TranscriptionResult(text=result.text, raw=_model_dump(result))

    def audio_speak(
        self,
        *,
        model: str,
        text: str,
        voice: str,
        response_format: str = "mp3",
        speed: Optional[float] = None,
    ) -> bytes:
        kwargs: dict[str, Any] = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": response_format,
        }
        if speed is not None:
            kwargs["speed"] = speed
        resp = self._call("tts.create_speech", self._client.tts.create_speech, **kwargs)
        # create_speech returns a streamed httpx.Response, same as get_video_content.
        return resp.read()

    # -- account ------------------------------------------------------------------

    def get_credits(self) -> CreditsInfo:
        result = self._call("credits.get_credits", self._client.credits.get_credits)
        data = result.data
        return CreditsInfo(
            total_credits=data.total_credits,
            total_usage=data.total_usage,
            balance=data.total_credits - data.total_usage,
            raw=_model_dump(result),
        )


def build_adapter(api_key: str, base_url: Optional[str] = None) -> OpenRouterAdapter:
    return OpenRouterAdapter(api_key, base_url)
