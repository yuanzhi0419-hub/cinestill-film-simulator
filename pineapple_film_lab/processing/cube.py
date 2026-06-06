from dataclasses import dataclass

import numpy as np


_MAX_TEXT_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class CubeLut:
    size: int
    table: np.ndarray
    domain_min: np.ndarray
    domain_max: np.ndarray

    def apply(self, image):
        pixels = np.asarray(image, dtype=np.float32)
        if pixels.ndim != 3 or pixels.shape[2] != 3:
            raise ValueError("image must have shape (height, width, 3)")
        if not np.isfinite(pixels).all():
            raise ValueError("image contains non-finite values")

        domain_span = self.domain_max - self.domain_min
        normalized = np.clip(
            (pixels - self.domain_min) / domain_span,
            0.0,
            1.0,
        )
        coordinates = normalized * (self.size - 1)
        lower = np.floor(coordinates).astype(np.int32)
        upper = np.minimum(lower + 1, self.size - 1)
        fraction = coordinates - lower

        r0, g0, b0 = lower[..., 0], lower[..., 1], lower[..., 2]
        r1, g1, b1 = upper[..., 0], upper[..., 1], upper[..., 2]
        fr = fraction[..., 0, None]
        fg = fraction[..., 1, None]
        fb = fraction[..., 2, None]

        c000 = self.table[r0, g0, b0]
        c001 = self.table[r0, g0, b1]
        c010 = self.table[r0, g1, b0]
        c011 = self.table[r0, g1, b1]
        c100 = self.table[r1, g0, b0]
        c101 = self.table[r1, g0, b1]
        c110 = self.table[r1, g1, b0]
        c111 = self.table[r1, g1, b1]

        c00 = c000 * (1.0 - fb) + c001 * fb
        c01 = c010 * (1.0 - fb) + c011 * fb
        c10 = c100 * (1.0 - fb) + c101 * fb
        c11 = c110 * (1.0 - fb) + c111 * fb
        c0 = c00 * (1.0 - fg) + c01 * fg
        c1 = c10 * (1.0 - fg) + c11 * fg
        result = c0 * (1.0 - fr) + c1 * fr
        return np.ascontiguousarray(np.clip(result, 0.0, 1.0), dtype=np.float32)


def parse_cube(text):
    if isinstance(text, bytes):
        if len(text) > _MAX_TEXT_BYTES:
            raise ValueError("cube file exceeds 10 MB")
        try:
            text = text.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise ValueError("cube file must be UTF-8 text") from error
    elif isinstance(text, str):
        if len(text.encode("utf-8")) > _MAX_TEXT_BYTES:
            raise ValueError("cube file exceeds 10 MB")
    else:
        raise ValueError("cube content must be text or bytes")

    size = None
    domain_min = np.zeros(3, dtype=np.float32)
    domain_max = np.ones(3, dtype=np.float32)
    rows = []

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        directive = parts[0].upper()

        if directive == "TITLE":
            continue
        if directive == "LUT_1D_SIZE":
            raise ValueError("1D LUT files are not supported")
        if directive == "LUT_3D_SIZE":
            if len(parts) != 2 or size is not None:
                raise ValueError("invalid LUT_3D_SIZE directive")
            try:
                size = int(parts[1])
            except ValueError as error:
                raise ValueError("LUT size must be an integer") from error
            if not 2 <= size <= 64:
                raise ValueError("LUT size must be between 2 and 64")
            continue
        if directive in {"DOMAIN_MIN", "DOMAIN_MAX"}:
            vector = _parse_vector(parts[1:], directive)
            if directive == "DOMAIN_MIN":
                domain_min = vector
            else:
                domain_max = vector
            continue
        if directive[0].isalpha():
            raise ValueError(
                f"unsupported directive on line {line_number}: {parts[0]}"
            )
        rows.append(_parse_vector(parts, f"data row {line_number}"))

    if size is None:
        raise ValueError("missing LUT_3D_SIZE directive")
    expected_rows = size**3
    if len(rows) != expected_rows:
        raise ValueError(
            f"cube row count must be {expected_rows}, got {len(rows)}"
        )
    if not np.all(domain_max > domain_min):
        raise ValueError("DOMAIN_MAX must be greater than DOMAIN_MIN")

    table = np.asarray(rows, dtype=np.float32).reshape(size, size, size, 3)
    return CubeLut(size, table, domain_min, domain_max)


def _parse_vector(values, label):
    if len(values) != 3:
        raise ValueError(f"{label} must contain three values")
    try:
        vector = np.asarray([float(value) for value in values], dtype=np.float32)
    except ValueError as error:
        raise ValueError(f"{label} contains an invalid number") from error
    if not np.isfinite(vector).all():
        raise ValueError(f"{label} values must be finite")
    return vector
