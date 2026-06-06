import pytest

from pineapple_film_lab.domain import EditParameters, JobStatus


def test_parameters_reject_out_of_range_values():
    with pytest.raises(ValueError, match="exposure"):
        EditParameters.from_mapping({"exposure": 9})


def test_parameters_supply_stable_defaults():
    params = EditParameters.from_mapping({})

    assert params.exposure == 0.0
    assert params.preset_strength == 1.0
    assert params.grain == 0.0


def test_parameters_reject_unknown_fields():
    with pytest.raises(ValueError, match="unknown parameters"):
        EditParameters.from_mapping({"unsupported": 1})


def test_job_status_has_terminal_states():
    assert JobStatus.COMPLETED.is_terminal
    assert JobStatus.FAILED.is_terminal
    assert JobStatus.CANCELLED.is_terminal
    assert not JobStatus.RUNNING.is_terminal
