import base64
from pathlib import Path
from typing import Optional


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


_MEDIA_TYPE_TO_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}


def save_b64_images(
    images_b64: list[str], media_types: list[Optional[str]], base_output: Path
) -> list[Path]:
    """Writes each base64 image to base_output, numbering the 2nd+ with a _N stem suffix.

    Models sometimes return a different format than the --output extension implies
    (e.g. JPEG bytes for a file named .png) - swap the suffix to match the actual
    returned media_type so downstream tools that sniff the extension (ffmpeg,
    browsers) don't silently choke on a mislabeled file.
    """
    paths = []
    for i, b64 in enumerate(images_b64):
        path = base_output if i == 0 else base_output.with_stem(f"{base_output.stem}_{i + 1}")
        media_type = media_types[i] if i < len(media_types) else None
        ext = _MEDIA_TYPE_TO_EXT.get(media_type or "")
        if ext and path.suffix.lower() != ext:
            path = path.with_suffix(ext)
        write_bytes(path, base64.b64decode(b64))
        paths.append(path)
    return paths
