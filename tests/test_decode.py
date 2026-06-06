from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from pineapple_film_lab.processing import decode
from pineapple_film_lab.processing.decode import DecodeError, decode_image


def png_bytes(mode="RGB"):
    color = (20, 40, 60, 128) if mode == "RGBA" else (20, 40, 60)
    image = Image.new(mode, (8, 6), color)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def oriented_jpeg_bytes():
    image = Image.new("RGB", (5, 3), (20, 40, 60))
    exif = Image.Exif()
    exif[274] = 6
    output = BytesIO()
    image.save(output, format="JPEG", exif=exif)
    return output.getvalue()


def test_decode_png_returns_float_rgb():
    decoded = decode_image(png_bytes())

    assert decoded.shape == (6, 8, 3)
    assert decoded.dtype == np.float32
    assert decoded.flags.c_contiguous
    assert 0.0 <= decoded.min() <= decoded.max() <= 1.0


def test_transparent_png_is_composited_on_neutral_background():
    decoded = decode_image(
        png_bytes("RGBA"),
        alpha_background=(0.5, 0.5, 0.5),
    )

    expected = np.array([0.29, 0.33, 0.37], dtype=np.float32)
    np.testing.assert_allclose(decoded[0, 0], expected, atol=0.015)


def test_exif_orientation_is_applied():
    decoded = decode_image(oriented_jpeg_bytes())

    assert decoded.shape == (5, 3, 3)


def test_invalid_bytes_raise_safe_decode_error(tmp_path):
    with pytest.raises(DecodeError, match="无法识别"):
        decode_image(b"not an image", raw_temp_dir=tmp_path)


def test_raw_fallback_uses_16_bit_camera_processing(monkeypatch, tmp_path):
    calls = {}

    class FakeRaw:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def postprocess(self, **kwargs):
            calls.update(kwargs)
            return np.array([[[0, 32768, 65535]]], dtype=np.uint16)

    def fake_imread(path):
        assert path.parent == tmp_path
        assert path.read_bytes() == b"raw bytes"
        return FakeRaw()

    monkeypatch.setattr(decode.rawpy, "imread", fake_imread)

    decoded = decode_image(b"raw bytes", raw_temp_dir=tmp_path)

    assert calls == {
        "use_camera_wb": True,
        "output_bps": 16,
        "no_auto_bright": True,
    }
    np.testing.assert_allclose(
        decoded,
        np.array([[[0.0, 32768 / 65535, 1.0]]], dtype=np.float32),
        atol=1e-6,
    )
    assert list(tmp_path.iterdir()) == []
