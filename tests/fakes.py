from typing import Any, Callable, Optional

from openrouter_cli.sdk_adapter import (
    ChatAnalysisResult,
    CreditsInfo,
    EmbeddingResult,
    ImageResult,
    RerankResult,
    TranscriptionResult,
    VideoJob,
)


class FakeAdapter:
    """Stands in for OpenRouterAdapter. Configure return values or an exception
    to raise, and inspect .calls afterwards for assertions."""

    def __init__(
        self,
        *,
        chat_result: Optional[ChatAnalysisResult] = None,
        image_result: Optional[ImageResult] = None,
        video_job: Optional[VideoJob] = None,
        video_status_sequence: Optional[list[VideoJob]] = None,
        video_content: bytes = b"",
        chat_models: Optional[list[dict]] = None,
        image_models: Optional[list[dict]] = None,
        video_models: Optional[list[dict]] = None,
        transcription_result: Optional[TranscriptionResult] = None,
        audio_content: bytes = b"",
        credits_info: Optional[CreditsInfo] = None,
        embedding_result: Optional[EmbeddingResult] = None,
        rerank_result: Optional[RerankResult] = None,
        model_info: Optional[dict] = None,
        providers: Optional[list[dict]] = None,
        generation_info: Optional[dict] = None,
        raise_exc: Optional[Exception] = None,
    ):
        self.chat_result = chat_result
        self.image_result = image_result
        self.video_job = video_job
        self._video_status_sequence = list(video_status_sequence or [])
        self.video_content = video_content
        self.chat_models = chat_models or []
        self.image_models = image_models or []
        self.video_models = video_models or []
        self.transcription_result = transcription_result
        self.audio_content = audio_content
        self.credits_info = credits_info
        self.embedding_result = embedding_result
        self.rerank_result = rerank_result
        self.model_info = model_info or {}
        self.providers = providers or []
        self.generation_info = generation_info or {}
        self.raise_exc = raise_exc
        self.calls: list[tuple[str, dict]] = []

    def __enter__(self) -> "FakeAdapter":
        return self

    def __exit__(self, *exc_info) -> None:
        pass

    def _maybe_raise(self):
        if self.raise_exc is not None:
            raise self.raise_exc

    def chat_send(self, **kwargs) -> ChatAnalysisResult:
        self.calls.append(("chat_send", kwargs))
        self._maybe_raise()
        return self.chat_result

    def list_chat_models(self, **kwargs) -> list[dict]:
        self.calls.append(("list_chat_models", kwargs))
        self._maybe_raise()
        return self.chat_models

    def image_generate(self, **kwargs) -> ImageResult:
        self.calls.append(("image_generate", kwargs))
        self._maybe_raise()
        return self.image_result

    def list_image_models(self) -> list[dict]:
        self.calls.append(("list_image_models", {}))
        self._maybe_raise()
        return self.image_models

    def video_generate(self, **kwargs) -> VideoJob:
        self.calls.append(("video_generate", kwargs))
        self._maybe_raise()
        return self.video_job

    def video_get_status(self, job_id: str) -> VideoJob:
        self.calls.append(("video_get_status", {"job_id": job_id}))
        self._maybe_raise()
        if self._video_status_sequence:
            return self._video_status_sequence.pop(0)
        return self.video_job

    def video_download(self, job_id: str, index: int = 0) -> bytes:
        self.calls.append(("video_download", {"job_id": job_id, "index": index}))
        self._maybe_raise()
        return self.video_content

    def list_video_models(self) -> list[dict]:
        self.calls.append(("list_video_models", {}))
        self._maybe_raise()
        return self.video_models

    def audio_transcribe(self, **kwargs) -> TranscriptionResult:
        self.calls.append(("audio_transcribe", kwargs))
        self._maybe_raise()
        return self.transcription_result

    def audio_speak(self, **kwargs) -> bytes:
        self.calls.append(("audio_speak", kwargs))
        self._maybe_raise()
        return self.audio_content

    def get_credits(self) -> CreditsInfo:
        self.calls.append(("get_credits", {}))
        self._maybe_raise()
        return self.credits_info

    def embeddings_generate(self, **kwargs) -> EmbeddingResult:
        self.calls.append(("embeddings_generate", kwargs))
        self._maybe_raise()
        return self.embedding_result

    def rerank(self, **kwargs) -> RerankResult:
        self.calls.append(("rerank", kwargs))
        self._maybe_raise()
        return self.rerank_result

    def get_model_info(self, **kwargs) -> dict:
        self.calls.append(("get_model_info", kwargs))
        self._maybe_raise()
        return self.model_info

    def list_providers(self) -> list[dict]:
        self.calls.append(("list_providers", {}))
        self._maybe_raise()
        return self.providers

    def get_generation(self, generation_id: str) -> dict:
        self.calls.append(("get_generation", {"generation_id": generation_id}))
        self._maybe_raise()
        return self.generation_info


def build_adapter_factory(fake: FakeAdapter) -> Callable[..., FakeAdapter]:
    def _build(api_key: str, base_url: Optional[str] = None) -> FakeAdapter:
        return fake

    return _build
