import base64
from pathlib import Path


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def save_b64_images(images_b64: list[str], base_output: Path) -> list[Path]:
    """Writes each base64 image to base_output, numbering the 2nd+ with a _N stem suffix."""
    paths = []
    for i, b64 in enumerate(images_b64):
        if i == 0:
            path = base_output
        else:
            path = base_output.with_stem(f"{base_output.stem}_{i + 1}")
        write_bytes(path, base64.b64decode(b64))
        paths.append(path)
    return paths
