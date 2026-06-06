import numpy as np
import pytest

from pineapple_film_lab.processing.cube import parse_cube


IDENTITY_2 = """
TITLE "Identity"
LUT_3D_SIZE 2
DOMAIN_MIN 0 0 0
DOMAIN_MAX 1 1 1
0 0 0
0 0 1
0 1 0
0 1 1
1 0 0
1 0 1
1 1 0
1 1 1
"""


def test_parse_identity_cube():
    lut = parse_cube(IDENTITY_2)

    assert lut.size == 2


def test_identity_cube_preserves_pixels():
    image = np.array([[[0.2, 0.4, 0.8]]], dtype=np.float32)

    result = parse_cube(IDENTITY_2).apply(image)

    np.testing.assert_allclose(result, image, atol=1e-5)


def test_parser_rejects_wrong_row_count():
    with pytest.raises(ValueError, match="row count"):
        parse_cube("LUT_3D_SIZE 2\n0 0 0")


def test_parser_rejects_1d_and_oversized_luts():
    with pytest.raises(ValueError, match="1D"):
        parse_cube("LUT_1D_SIZE 2\n0 0 0\n1 1 1")
    with pytest.raises(ValueError, match="between 2 and 64"):
        parse_cube("LUT_3D_SIZE 65")


def test_parser_rejects_unknown_directives_and_non_finite_values():
    with pytest.raises(ValueError, match="unsupported directive"):
        parse_cube("LUT_3D_SIZE 2\nFOO 1")
    with pytest.raises(ValueError, match="finite"):
        parse_cube(IDENTITY_2.replace("1 1 1", "nan 1 1"))


def test_domain_is_applied_before_interpolation():
    text = IDENTITY_2.replace("DOMAIN_MAX 1 1 1", "DOMAIN_MAX 2 2 2")
    image = np.array([[[1.0, 0.5, 2.0]]], dtype=np.float32)

    result = parse_cube(text).apply(image)

    np.testing.assert_allclose(result, [[[0.5, 0.25, 1.0]]], atol=1e-5)
