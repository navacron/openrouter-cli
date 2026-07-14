import base64

from openrouter_cli import io_utils


def test_save_b64_images_keeps_matching_extension(tmp_path):
    out = tmp_path / "scene.png"
    b64 = base64.b64encode(b"pngbytes").decode()

    paths = io_utils.save_b64_images([b64], ["image/png"], out)

    assert paths == [out]
    assert out.read_bytes() == b"pngbytes"


def test_save_b64_images_corrects_mismatched_extension(tmp_path):
    out = tmp_path / "scene.png"
    b64 = base64.b64encode(b"jpegbytes").decode()

    paths = io_utils.save_b64_images([b64], ["image/jpeg"], out)

    assert paths == [tmp_path / "scene.jpg"]
    assert paths[0].read_bytes() == b"jpegbytes"
    assert not out.exists()


def test_save_b64_images_unknown_media_type_keeps_requested_extension(tmp_path):
    out = tmp_path / "scene.png"
    b64 = base64.b64encode(b"data").decode()

    paths = io_utils.save_b64_images([b64], [None], out)

    assert paths == [out]


def test_save_b64_images_numbers_second_and_later_with_corrected_extensions(tmp_path):
    out = tmp_path / "logo.png"
    b64s = [base64.b64encode(d).decode() for d in (b"a", b"b", b"c")]

    paths = io_utils.save_b64_images(b64s, ["image/png", "image/jpeg", "image/png"], out)

    assert paths == [tmp_path / "logo.png", tmp_path / "logo_2.jpg", tmp_path / "logo_3.png"]
    assert paths[1].read_bytes() == b"b"
