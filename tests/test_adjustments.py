import numpy as np

from pineapple_film_lab.processing.adjustments import (
    apply_exposure,
    apply_saturation,
    apply_temperature,
    apply_tone,
)


def test_zero_adjustments_are_identity():
    image = np.full((4, 4, 3), 0.4, dtype=np.float32)
    result = apply_saturation(
        apply_temperature(
            apply_tone(apply_exposure(image, 0), 0, 0, 0),
            0,
        ),
        0,
    )

    np.testing.assert_allclose(result, image, atol=1e-6)


def test_positive_exposure_doubles_linear_values():
    image = np.full((1, 1, 3), 0.2, dtype=np.float32)

    np.testing.assert_allclose(apply_exposure(image, 1), 0.4, atol=1e-6)


def test_positive_contrast_expands_values_around_middle_gray():
    image = np.array([[[0.25, 0.5, 0.75]]], dtype=np.float32)

    result = apply_tone(image, contrast=1, highlights=0, shadows=0)

    assert result[0, 0, 0] < image[0, 0, 0]
    assert result[0, 0, 2] > image[0, 0, 2]


def test_highlights_and_shadows_target_different_luminance_regions():
    dark = np.full((1, 1, 3), 0.1, dtype=np.float32)
    bright = np.full((1, 1, 3), 0.9, dtype=np.float32)

    lifted_shadow = apply_tone(dark, 0, 0, 1)
    lifted_highlight = apply_tone(bright, 0, 1, 0)

    assert lifted_shadow.mean() > dark.mean()
    assert lifted_highlight.mean() > bright.mean()
    np.testing.assert_allclose(
        apply_tone(bright, 0, 0, 1),
        bright,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        apply_tone(dark, 0, 1, 0),
        dark,
        atol=1e-6,
    )


def test_positive_temperature_warms_neutral_pixel():
    image = np.full((1, 1, 3), 0.5, dtype=np.float32)

    result = apply_temperature(image, 1)

    assert result[0, 0, 0] > result[0, 0, 2]
    assert abs(float(result.mean()) - 0.5) < 0.03


def test_saturation_reduction_and_increase_are_monotonic():
    image = np.array([[[0.2, 0.5, 0.8]]], dtype=np.float32)

    desaturated = apply_saturation(image, -1)
    saturated = apply_saturation(image, 1)

    assert np.ptp(desaturated[0, 0]) < np.ptp(image[0, 0])
    assert np.ptp(saturated[0, 0]) > np.ptp(image[0, 0])


def test_adjustments_do_not_mutate_input():
    image = np.full((3, 3, 3), 0.4, dtype=np.float32)
    original = image.copy()

    apply_tone(image, 0.5, -0.2, 0.3)

    np.testing.assert_array_equal(image, original)
