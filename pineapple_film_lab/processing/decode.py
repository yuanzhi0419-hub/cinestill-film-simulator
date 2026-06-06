from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
import rawpy
from PIL import Image, ImageOps, UnidentifiedImageError


class DecodeError(ValueError):
    pass


def decode_image(
    data,
    *,
    alpha_background=(0.18, 0.18, 0.18),
    raw_temp_dir=None,
):
    if not isinstance(data, (bytes, bytearray, memoryview)) or not data:
        raise DecodeError("无法识别图片内容")

    raw_bytes = bytes(data)
    try:
        decoded = _decode_with_pillow(raw_bytes, alpha_background)
    except (UnidentifiedImageError, OSError, ValueError):
        decoded = _decode_with_rawpy(raw_bytes, raw_temp_dir)
    return _as_float_rgb(decoded)


def _decode_with_pillow(data, alpha_background):
    background = _validate_background(alpha_background)
    with Image.open(BytesIO(data)) as source:
        source.load()
        image = ImageOps.exif_transpose(source)
        if "A" in image.getbands() or "transparency" in image.info:
            foreground = image.convert("RGBA")
            color = tuple(round(channel * 255) for channel in background) + (255,)
            canvas = Image.new("RGBA", foreground.size, color)
            image = Image.alpha_composite(canvas, foreground).convert("RGB")
        else:
            image = image.convert("RGB")
        return np.asarray(image, dtype=np.uint8)


def _decode_with_rawpy(data, raw_temp_dir):
    directory = None
    if raw_temp_dir is not None:
        directory = Path(raw_temp_dir).expanduser().resolve()
        directory.mkdir(parents=True, exist_ok=True)

    temporary_path = None
    try:
        with NamedTemporaryFile(
            mode="wb",
            suffix=".raw",
            dir=directory,
            delete=False,
        ) as temporary:
            temporary.write(data)
            temporary_path = Path(temporary.name)

        with rawpy.imread(temporary_path) as raw:
            return raw.postprocess(
                use_camera_wb=True,
                output_bps=16,
                no_auto_bright=True,
            )
    except Exception as error:
        raise DecodeError("无法识别图片内容或不支持该 RAW 格式") from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _validate_background(background):
    if len(background) != 3:
        raise ValueError("alpha background must contain three channels")
    result = tuple(float(channel) for channel in background)
    if not all(0.0 <= channel <= 1.0 for channel in result):
        raise ValueError("alpha background channels must be between 0 and 1")
    return result


def _as_float_rgb(image):
    array = np.asarray(image)
    if array.ndim != 3 or array.shape[2] != 3:
        raise DecodeError("图片必须能够转换为 RGB")

    if np.issubdtype(array.dtype, np.integer):
        maximum = np.iinfo(array.dtype).max
        normalized = array.astype(np.float32) / float(maximum)
    else:
        normalized = array.astype(np.float32)

    if not np.isfinite(normalized).all():
        raise DecodeError("图片包含无效像素值")
    return np.ascontiguousarray(np.clip(normalized, 0.0, 1.0))
