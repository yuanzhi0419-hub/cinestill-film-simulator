from dataclasses import asdict

from pineapple_film_lab.domain import EditParameters


PRESETS = {
    "night-walk": {
        "contrast": 0.18,
        "temperature": -0.08,
        "saturation": 0.08,
        "halation": 0.35,
        "grain": 0.18,
    },
    "morning-light": {
        "exposure": 0.15,
        "contrast": -0.08,
        "temperature": 0.16,
        "highlights": -0.12,
        "grain": 0.08,
    },
    "natural-negative": {
        "contrast": 0.06,
        "saturation": -0.05,
        "highlights": -0.08,
        "shadows": 0.05,
        "grain": 0.10,
    },
    "soft-haze": {
        "contrast": -0.18,
        "highlights": -0.10,
        "shadows": 0.12,
        "halation": 0.16,
        "grain": 0.06,
    },
    "documentary-bw": {
        "saturation": -1.0,
        "contrast": 0.20,
        "grain": 0.28,
        "vignette": 0.16,
    },
}

PRESET_LABELS = {
    "night-walk": "夜行",
    "morning-light": "清晨",
    "natural-negative": "自然负片",
    "soft-haze": "柔雾",
    "documentary-bw": "黑白纪实",
}

_NUMERIC_FIELDS = {
    "exposure",
    "contrast",
    "highlights",
    "shadows",
    "temperature",
    "saturation",
    "halation",
    "grain",
    "vignette",
}


def resolve_parameters(parameters):
    try:
        preset_values = PRESETS[parameters.preset]
    except KeyError as error:
        raise ValueError(f"unknown preset: {parameters.preset}") from error

    resolved = asdict(parameters)
    for name in _NUMERIC_FIELDS:
        resolved[name] = getattr(parameters, name) + (
            preset_values.get(name, 0.0) * parameters.preset_strength
        )

    resolved["preset_strength"] = 0.0
    for name in ("halation", "grain", "vignette"):
        resolved[name] = min(1.0, max(0.0, resolved[name]))
    for name in (
        "contrast",
        "highlights",
        "shadows",
        "temperature",
        "saturation",
    ):
        resolved[name] = min(1.0, max(-1.0, resolved[name]))
    resolved["exposure"] = min(3.0, max(-3.0, resolved["exposure"]))
    return EditParameters.from_mapping(resolved)


def serialize_presets():
    return [
        {"id": preset_id, "label": PRESET_LABELS[preset_id]}
        for preset_id in PRESETS
    ]

