import base64
import mimetypes
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx

from openrouter_cli.errors import ValidationError

MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024  # 100MB safety cap for remote fetches

# Short format tokens accepted by the chat `input_audio` content part, keyed by
# the mimetypes subtype we're likely to see.
_AUDIO_SUBTYPE_TO_FORMAT = {
    "mpeg": "mp3",
    "mp3": "mp3",
    "wav": "wav",
    "x-wav": "wav",
    "flac": "flac",
    "x-flac": "flac",
    "mp4": "m4a",
    "m4a": "m4a",
    "aac": "aac",
    "ogg": "ogg",
    "aiff": "aiff",
    "x-aiff": "aiff",
}

VALID_KINDS = ("image", "video", "audio", "file")


def is_url(path_or_url: str) -> bool:
    return urlparse(path_or_url).scheme in ("http", "https")


def guess_mime(path_or_url: str) -> Optional[str]:
    mime, _ = mimetypes.guess_type(path_or_url)
    return mime


def detect_kind(path_or_url: str, override: Optional[str] = None) -> tuple[str, str]:
    """Returns (kind, mime_type). kind is one of VALID_KINDS."""
    if override:
        if override not in VALID_KINDS:
            raise ValidationError(
                f"--type must be one of {', '.join(VALID_KINDS)}, got {override!r}"
            )
        mime = guess_mime(path_or_url) or _default_mime_for_kind(override)
        return override, mime

    mime = guess_mime(path_or_url)
    if mime is None:
        raise ValidationError(
            f"Could not detect the content type of {path_or_url!r} from its extension. "
            "Pass --type {image,video,audio,file} to override."
        )
    if mime == "application/pdf":
        return "file", mime
    top_level = mime.split("/", 1)[0]
    if top_level in ("image", "video", "audio"):
        return top_level, mime
    return "file", mime


def _default_mime_for_kind(kind: str) -> str:
    return {
        "image": "image/png",
        "video": "video/mp4",
        "audio": "audio/mpeg",
        "file": "application/pdf",
    }[kind]


def load_bytes(path_or_url: str, max_bytes: int = MAX_DOWNLOAD_BYTES) -> bytes:
    if is_url(path_or_url):
        with httpx.stream("GET", path_or_url, follow_redirects=True, timeout=60.0) as resp:
            resp.raise_for_status()
            chunks = []
            total = 0
            for chunk in resp.iter_bytes():
                total += len(chunk)
                if total > max_bytes:
                    raise ValidationError(
                        f"{path_or_url} exceeds the {max_bytes} byte download cap"
                    )
                chunks.append(chunk)
            return b"".join(chunks)

    path = Path(path_or_url)
    if not path.is_file():
        raise ValidationError(f"File not found: {path_or_url}")
    data = path.read_bytes()
    if len(data) > max_bytes:
        raise ValidationError(f"{path_or_url} exceeds the {max_bytes} byte size cap")
    return data


def to_data_uri(data: bytes, mime: str) -> str:
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def normalize_audio_format(mime: str) -> str:
    subtype = mime.split("/", 1)[-1] if "/" in mime else mime
    return _AUDIO_SUBTYPE_TO_FORMAT.get(subtype, subtype)


def build_content_part(path_or_url: str, kind: str, mime: str) -> dict:
    """Builds the OpenAI-compatible content-part dict for the given kind.

    image_url/video_url/file.file_data all accept either a plain URL or a
    data: URI directly (confirmed against the SDK's component schema), so
    those pass URLs through untouched. input_audio only accepts base64 data
    with no url field, so audio is always downloaded and encoded.
    """
    if kind == "image":
        url = path_or_url if is_url(path_or_url) else to_data_uri(load_bytes(path_or_url), mime)
        return {"type": "image_url", "image_url": {"url": url}}

    if kind == "video":
        url = path_or_url if is_url(path_or_url) else to_data_uri(load_bytes(path_or_url), mime)
        return {"type": "video_url", "video_url": {"url": url}}

    if kind == "file":
        url = path_or_url if is_url(path_or_url) else to_data_uri(load_bytes(path_or_url), mime)
        filename = Path(urlparse(path_or_url).path if is_url(path_or_url) else path_or_url).name
        return {"type": "file", "file": {"filename": filename, "file_data": url}}

    if kind == "audio":
        data = load_bytes(path_or_url)
        return {
            "type": "input_audio",
            "input_audio": {
                "data": base64.b64encode(data).decode("ascii"),
                "format": normalize_audio_format(mime),
            },
        }

    raise ValidationError(f"Unsupported content kind: {kind!r}")
