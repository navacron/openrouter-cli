import base64

import pytest

from openrouter_cli import mime_utils
from openrouter_cli.errors import ValidationError


def test_detect_kind_image():
    kind, mime = mime_utils.detect_kind("photo.jpg")
    assert kind == "image"
    assert mime == "image/jpeg"


def test_detect_kind_video():
    kind, mime = mime_utils.detect_kind("kite.mp4")
    assert kind == "video"
    assert mime == "video/mp4"


def test_detect_kind_audio():
    kind, mime = mime_utils.detect_kind("clip.mp3")
    assert kind == "audio"
    assert mime == "audio/mpeg"


def test_detect_kind_pdf_maps_to_file():
    kind, mime = mime_utils.detect_kind("doc.pdf")
    assert kind == "file"
    assert mime == "application/pdf"


def test_detect_kind_unknown_extension_raises():
    with pytest.raises(ValidationError):
        mime_utils.detect_kind("mystery.qqzznope")


def test_detect_kind_override_bypasses_guessing():
    kind, mime = mime_utils.detect_kind("mystery.qqzznope", override="image")
    assert kind == "image"


def test_detect_kind_invalid_override_raises():
    with pytest.raises(ValidationError):
        mime_utils.detect_kind("a.jpg", override="not-a-kind")


def test_is_url():
    assert mime_utils.is_url("https://example.com/a.jpg")
    assert mime_utils.is_url("http://example.com/a.jpg")
    assert not mime_utils.is_url("./local/a.jpg")
    assert not mime_utils.is_url("a.jpg")


def test_build_content_part_image_local(tmp_path):
    f = tmp_path / "a.png"
    f.write_bytes(b"fakepngbytes")
    part = mime_utils.build_content_part(str(f), "image", "image/png")
    assert part["type"] == "image_url"
    assert part["image_url"]["url"].startswith("data:image/png;base64,")
    decoded = base64.b64decode(part["image_url"]["url"].split(",", 1)[1])
    assert decoded == b"fakepngbytes"


def test_build_content_part_image_url_passthrough():
    url = "https://example.com/a.jpg"
    part = mime_utils.build_content_part(url, "image", "image/jpeg")
    assert part == {"type": "image_url", "image_url": {"url": url}}


def test_build_content_part_video_local(tmp_path):
    f = tmp_path / "kite.mp4"
    f.write_bytes(b"fakevideobytes")
    part = mime_utils.build_content_part(str(f), "video", "video/mp4")
    assert part["type"] == "video_url"
    assert part["video_url"]["url"].startswith("data:video/mp4;base64,")


def test_build_content_part_file_local(tmp_path):
    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF-fake")
    part = mime_utils.build_content_part(str(f), "file", "application/pdf")
    assert part["type"] == "file"
    assert part["file"]["filename"] == "doc.pdf"
    assert part["file"]["file_data"].startswith("data:application/pdf;base64,")


def test_build_content_part_audio_local(tmp_path):
    f = tmp_path / "clip.mp3"
    f.write_bytes(b"fakeaudiobytes")
    part = mime_utils.build_content_part(str(f), "audio", "audio/mpeg")
    assert part["type"] == "input_audio"
    assert part["input_audio"]["format"] == "mp3"
    decoded = base64.b64decode(part["input_audio"]["data"])
    assert decoded == b"fakeaudiobytes"


def test_load_bytes_missing_file_raises():
    with pytest.raises(ValidationError):
        mime_utils.load_bytes("/no/such/file.jpg")
