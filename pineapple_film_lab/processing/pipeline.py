import numpy as np

from .adjustments import (
    apply_exposure,
    apply_saturation,
    apply_temperature,
    apply_tone,
)
from .effects import add_grain, add_halation, add_vignette
from .presets import resolve_parameters


def process_image(image, parameters, *, grain_seed=0, lut=None):
    resolved = resolve_parameters(parameters)
    result = apply_exposure(image, resolved.exposure)
    result = apply_tone(
        result,
        resolved.contrast,
        resolved.highlights,
        resolved.shadows,
    )
    result = apply_temperature(result, resolved.temperature)
    result = apply_saturation(result, resolved.saturation)
    if lut is not None:
        result = lut.apply(result)
    result = add_halation(result, resolved.halation)
    result = add_grain(result, resolved.grain, seed=grain_seed)
    result = add_vignette(result, resolved.vignette)
    return np.ascontiguousarray(np.clip(result, 0.0, 1.0), dtype=np.float32)
