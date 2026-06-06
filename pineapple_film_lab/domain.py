from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class JobStatus(str, Enum):
    PENDING = "pending"
    DECODING = "decoding"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self):
        return self in {
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        }


_PARAMETER_RANGES = {
    "preset_strength": (0.0, 1.0),
    "exposure": (-3.0, 3.0),
    "contrast": (-1.0, 1.0),
    "highlights": (-1.0, 1.0),
    "shadows": (-1.0, 1.0),
    "temperature": (-1.0, 1.0),
    "saturation": (-1.0, 1.0),
    "halation": (0.0, 1.0),
    "grain": (0.0, 1.0),
    "vignette": (0.0, 1.0),
}


@dataclass(frozen=True)
class EditParameters:
    preset: str = "natural-negative"
    preset_strength: float = 1.0
    exposure: float = 0.0
    contrast: float = 0.0
    highlights: float = 0.0
    shadows: float = 0.0
    temperature: float = 0.0
    saturation: float = 0.0
    halation: float = 0.0
    grain: float = 0.0
    vignette: float = 0.0
    lut_id: str | None = None

    @classmethod
    def from_mapping(cls, values: Mapping):
        allowed = set(cls.__dataclass_fields__)
        unknown = set(values) - allowed
        if unknown:
            names = ", ".join(sorted(unknown))
            raise ValueError(f"unknown parameters: {names}")

        normalized = dict(values)
        for name in _PARAMETER_RANGES.keys() & values.keys():
            try:
                normalized[name] = float(values[name])
            except (TypeError, ValueError) as error:
                raise ValueError(f"{name} must be numeric") from error

        result = cls(**normalized)
        if not isinstance(result.preset, str) or not result.preset:
            raise ValueError("preset must be a non-empty string")
        if result.lut_id is not None and not isinstance(result.lut_id, str):
            raise ValueError("lut_id must be a string or null")

        for name, (minimum, maximum) in _PARAMETER_RANGES.items():
            value = getattr(result, name)
            if not minimum <= value <= maximum:
                raise ValueError(
                    f"{name} must be between {minimum} and {maximum}"
                )

        return result
