import pytest

from pineapple_film_lab.processing.presets import PRESETS, resolve_parameters
from pineapple_film_lab.domain import EditParameters


def test_expected_original_presets_exist():
    assert set(PRESETS) == {
        "night-walk",
        "morning-light",
        "natural-negative",
        "soft-haze",
        "documentary-bw",
    }


def test_preset_strength_blends_with_user_adjustments():
    params = EditParameters(
        preset="night-walk",
        preset_strength=0.5,
        exposure=0.2,
    )

    resolved = resolve_parameters(params)

    assert resolved.exposure == pytest.approx(0.2)
    assert resolved.contrast == pytest.approx(0.09)
    assert resolved.halation == pytest.approx(0.175)
    assert resolved.preset_strength == 0.0


def test_unknown_preset_is_rejected():
    with pytest.raises(ValueError, match="unknown preset"):
        resolve_parameters(EditParameters(preset="missing"))

