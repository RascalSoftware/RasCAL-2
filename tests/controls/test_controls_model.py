"""Tests for the Controls fit settings model."""

import pytest
from pydantic import ValidationError

from rascal2.widgets.controls.model import FitSettingsModel
from tests.controls.control_mocks import MockPresenter

PROCEDURES = ["calculate", "simplex", "de", "ns", "dream"]


@pytest.fixture
def model():
    return lambda procedure: FitSettingsModel(MockPresenter())


def test_get_data(model):
    """Test that the Controls data is corectly retrieved."""
    md = model("dream")
    fields = list(md.model_fields.keys())
    values = [getattr(md.controls, field) for field in fields]

    assert [md.data(field) for field in fields] == values


@pytest.mark.parametrize(["param", "value"], [("nSamples", 50), ("calcSldDuringFit", True), ("parallel", "contrasts")])
def test_set_data(model, param, value):
    """Check that setting values are correctly propagated to the Controls object."""
    md = model("dream")
    assert md.setData(param, value)

    assert getattr(md.presenter.model.controls, param) == value


@pytest.mark.parametrize(
    ["param", "value"], [("nSamples", "???"), ("calcSldDuringFit", "something"), ("parallel", "bad parallel setting")]
)
def test_validation_error(model, param, value):
    """Test that data is not changed if invalid data is passed to set."""
    md = model("dream")

    assert md.setData(param, value) is False
    with pytest.raises(ValidationError, match=f"{param}"):
        raise md.last_validation_error
