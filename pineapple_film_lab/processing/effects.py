import math

import cv2
import numpy as np


_LUMINANCE_WEIGHTS = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
_HALATION_TINT = np.array([1.0, 0.3, 0.12], dtype=np.float32)


def add_halation(image, amount):
    strength = _effect_amount("halation", amount)
    result = _prepare_image(image)
    if strength == 0.0:
        return result

    luminance = np.sum(result * _LUMINANCE_WEIGHTS, axis=2)
    highlight_mask = _smoothstep(0.72, 0.98, luminance)
    sigma = max(0.8, min(result.shape[:2]) * 0.025)
    spread = cv2.GaussianBlur(
        highlight_mask,
        (0, 0),
        sigmaX=sigma,
        sigmaY=sigma,
        borderType=cv2.BORDER_REFLECT101,
    )
    energy = spread[..., None] * _HALATION_TINT * (0.65 * strength)
    return _finish(result + energy)


def add_grain(image, amount, *, seed=0):
    strength = _effect_amount("grain", amount)
    result = _prepare_image(image)
    if strength == 0.0:
        return result

    generator = np.random.default_rng(seed)
    height, width = result.shape[:2]
    monochrome = generator.normal(0.0, 1.0, (height, width, 1))
    chromatic = generator.normal(0.0, 1.0, (height, width, 3))
    noise = 0.9 * monochrome + 0.1 * chromatic

    luminance = np.sum(result * _LUMINANCE_WEIGHTS, axis=2, keepdims=True)
    modulation = 0.65 + 0.35 * (1.0 - luminance)
    return _finish(result + noise * modulation * (0.06 * strength))


def add_vignette(image, amount):
    strength = _effect_amount("vignette", amount)
    result = _prepare_image(image)
    if strength == 0.0:
        return result

    height, width = result.shape[:2]
    y = np.linspace(-1.0, 1.0, height, dtype=np.float32)
    x = np.linspace(-1.0, 1.0, width, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    distance = np.sqrt(xx * xx + yy * yy) / np.sqrt(2.0)
    edge_mask = _smoothstep(0.3, 1.0, distance)
    attenuation = 1.0 - edge_mask[..., None] * (0.65 * strength)
    return _finish(result * attenuation)


def _prepare_image(image):
    array = np.asarray(image, dtype=np.float32)
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError("image must have shape (height, width, 3)")
    if not np.isfinite(array).all():
        raise ValueError("image contains non-finite values")
    return np.ascontiguousarray(array.copy())


def _finish(image):
    return np.ascontiguousarray(np.clip(image, 0.0, 1.0), dtype=np.float32)


def _effect_amount(name, value):
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be numeric") from error
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")
    return result


def _smoothstep(edge0, edge1, values):
    normalized = np.clip((values - edge0) / (edge1 - edge0), 0.0, 1.0)
    return normalized * normalized * (3.0 - 2.0 * normalized)
