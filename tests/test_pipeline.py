import numpy as np

from pineapple_film_lab.domain import EditParameters
from pineapple_film_lab.processing import pipeline
from pineapple_film_lab.processing.pipeline import process_image


def test_default_pipeline_is_bounded_and_same_shape():
    image = np.full((24, 32, 3), 0.5, dtype=np.float32)

    result = process_image(image, EditParameters())

    assert result.shape == image.shape
    assert result.dtype == np.float32
    assert 0.0 <= result.min() <= result.max() <= 1.0


def test_pipeline_uses_fixed_processing_order(monkeypatch):
    calls = []
    image = np.full((2, 2, 3), 0.5, dtype=np.float32)

    def record(name):
        def wrapper(value, *args, **kwargs):
            calls.append(name)
            return value

        return wrapper

    monkeypatch.setattr(pipeline, "apply_exposure", record("exposure"))
    monkeypatch.setattr(pipeline, "apply_tone", record("tone"))
    monkeypatch.setattr(pipeline, "apply_temperature", record("temperature"))
    monkeypatch.setattr(pipeline, "apply_saturation", record("saturation"))
    monkeypatch.setattr(pipeline, "add_halation", record("halation"))
    monkeypatch.setattr(pipeline, "add_grain", record("grain"))
    monkeypatch.setattr(pipeline, "add_vignette", record("vignette"))

    process_image(image, EditParameters(), grain_seed=4)

    assert calls == [
        "exposure",
        "tone",
        "temperature",
        "saturation",
        "halation",
        "grain",
        "vignette",
    ]
