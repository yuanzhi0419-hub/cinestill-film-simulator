import numpy as np

from pineapple_film_lab.processing.effects import (
    add_grain,
    add_halation,
    add_vignette,
)


def test_halation_only_changes_bright_neighborhood():
    image = np.zeros((31, 31, 3), dtype=np.float32)
    image[15, 15] = 1.0

    result = add_halation(image, amount=1.0)

    assert result[15, 16, 0] > image[15, 16, 0]
    assert result[15, 16, 0] > result[15, 16, 2]
    assert result[0, 0].max() < 0.01


def test_halation_ignores_dark_image():
    image = np.full((17, 17, 3), 0.2, dtype=np.float32)

    np.testing.assert_allclose(add_halation(image, 1), image, atol=1e-6)


def test_grain_is_repeatable_with_seed():
    image = np.full((16, 16, 3), 0.5, dtype=np.float32)

    first = add_grain(image, amount=0.5, seed=7)
    second = add_grain(image, amount=0.5, seed=7)

    np.testing.assert_allclose(first, second)
    assert not np.array_equal(first, image)


def test_vignette_preserves_center_more_than_corner():
    image = np.ones((21, 21, 3), dtype=np.float32)

    result = add_vignette(image, amount=1.0)

    assert result[10, 10, 0] > result[0, 0, 0]
    np.testing.assert_allclose(result[10, 10], image[10, 10], atol=1e-6)


def test_zero_effect_amounts_are_identity():
    image = np.full((12, 18, 3), 0.4, dtype=np.float32)

    np.testing.assert_array_equal(add_halation(image, 0), image)
    np.testing.assert_array_equal(add_grain(image, 0, seed=4), image)
    np.testing.assert_array_equal(add_vignette(image, 0), image)


def test_effects_do_not_mutate_input_and_remain_bounded():
    image = np.full((24, 24, 3), 0.8, dtype=np.float32)
    original = image.copy()

    result = add_vignette(
        add_grain(add_halation(image, 0.6), 0.5, seed=3),
        0.4,
    )

    np.testing.assert_array_equal(image, original)
    assert result.dtype == np.float32
    assert 0.0 <= result.min() <= result.max() <= 1.0
