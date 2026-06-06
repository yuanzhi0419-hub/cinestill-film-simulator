import math

import numpy as np


_LUMINANCE_WEIGHTS = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def apply_exposure(image, stops):
    value = _bounded_scalar("exposure", stops, -3.0, 3.0)
    result = _prepare_image(image) * np.float32(2.0**value)
    return _finish(result)


def apply_tone(image, contrast, highlights, shadows):
    contrast_value = _bounded_scalar("contrast", contrast, -1.0, 1.0)
    highlight_value = _bounded_scalar("highlights", highlights, -1.0, 1.0)
    shadow_value = _bounded_scalar("shadows", shadows, -1.0, 1.0)
    result = _prepare_image(image)

    curved = result * result * (3.0 - 2.0 * result)
    result = result + contrast_value * (curved - result)

    luminance = _luminance(result)
    highlight_mask = _smoothstep(0.5, 1.0, luminance)[..., None]
    shadow_mask = (1.0 - _smoothstep(0.0, 0.5, luminance))[..., None]
    result = _apply_masked_adjustment(result, highlight_mask, highlight_value)
    result = _apply_masked_adjustment(result, shadow_mask, shadow_value)
    return _finish(result)


def apply_temperature(image, amount):
    value = _bounded_scalar("temperature", amount, -1.0, 1.0)
    result = _prepare_image(image)
    if value == 0.0:
        return result

    before_luminance = _luminance(result)
    gains = np.array(
        [1.0 + 0.18 * value, 1.0, 1.0 - 0.18 * value],
        dtype=np.float32,
    )
    warmed = result * gains
    after_luminance = _luminance(warmed)
    scale = before_luminance / np.maximum(after_luminance, 1e-6)
    return _finish(warmed * scale[..., None])


def apply_saturation(image, amount):
    value = _bounded_scalar("saturation", amount, -1.0, 1.0)
    result = _prepare_image(image)
    luminance = _luminance(result)[..., None]
    factor = 1.0 + value
    return _finish(luminance + (result - luminance) * factor)


def _prepare_image(image):
    array = np.asarray(image, dtype=np.float32)
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError("image must have shape (height, width, 3)")
    if not np.isfinite(array).all():
        raise ValueError("image contains non-finite values")
    return np.ascontiguousarray(array.copy())


def _finish(image):
    return np.ascontiguousarray(np.clip(image, 0.0, 1.0), dtype=np.float32)


def _bounded_scalar(name, value, minimum, maximum):
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be numeric") from error
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return result


def _luminance(image):
    return np.sum(image * _LUMINANCE_WEIGHTS, axis=2)


def _smoothstep(edge0, edge1, values):
    normalized = np.clip((values - edge0) / (edge1 - edge0), 0.0, 1.0)
    return normalized * normalized * (3.0 - 2.0 * normalized)


def _apply_masked_adjustment(image, mask, amount):
    if amount >= 0.0:
        return image + amount * mask * (1.0 - image) * 0.5
    return image + amount * mask * image * 0.5
