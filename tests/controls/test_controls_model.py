"""Tests for the Controls fit settings model."""

from copy import copy

import pytest
from pydantic_core import ValidationError
from PyQt6 import QtCore
from RATapi.controls import fields

from rascal2.widgets.controls.model import FitSettingsModel
from tests.controls.control_mocks import MockPresenter

PROCEDURES = ["calculate", "simplex", "de", "ns", "dream"]


@pytest.fixture
def model():
    return lambda procedure: FitSettingsModel(MockPresenter(procedure))


@pytest.mark.parametrize("procedure", PROCEDURES)
def test_model_size(model, procedure):
    """Test that the model is the correct size."""
    md = model(procedure)
    rows = len(fields[procedure]) - 1
    assert md.columnCount() == 1
    assert md.rowCount() == rows


@pytest.mark.parametrize("procedure", PROCEDURES)
def test_header_data(model, procedure):
    """Test that headers are as expected."""
    md = model(procedure)
    headers = copy(fields[procedure])
    headers.remove("procedure")
    assert len(headers) == md.rowCount()
    assert [
        md.headerData(i, QtCore.Qt.Orientation.Vertical, QtCore.Qt.ItemDataRole.DisplayRole)
        for i in range(0, len(headers))
    ] == headers


def test_get_data(model):
    """Test that the Controls data is corectly retrieved."""
    md = model("dream")
    params = copy(fields["dream"])
    params.remove("procedure")

    # Qt returns data in string format, so convert to str
    vals = [str(getattr(md.presenter.model.controls, param)) for param in params]

    model_index = lambda i: md.createIndex(i, 0)  # noqa: E731 (lambda expressions not allowed)

    assert len(vals) == md.rowCount()
    assert [md.data(model_index(i), QtCore.Qt.ItemDataRole.DisplayRole) for i in range(0, len(vals))] == vals


@pytest.mark.parametrize(["index", "value"], [(5, 50), (1, True), (0, "contrasts")])
def test_set_data(model, index, value):
    """Check that setting values are correctly propagated to the Controls object."""
    md = model("dream")
    params = copy(fields["dream"])
    params.remove("procedure")
    expected_attr = params[index]

    model_index = lambda i: md.createIndex(i, 0)  # noqa: E731 (lambda expressions not allowed)

    md.setData(model_index(index), str(value), QtCore.Qt.ItemDataRole.EditRole)

    assert getattr(md.presenter.model.controls, expected_attr) == value


@pytest.mark.parametrize(["index", "value"], [(5, "???"), (1, "something"), (0, "bad parallel setting")])
def test_validation_error(model, index, value):
    """Test that an error is properly given to the Presenter if a bad value is given to setData."""
    md = model("dream")
    model_index = lambda i: md.createIndex(i, 0)  # noqa: E731 (lambda expressions not allowed)

    with pytest.raises(ValidationError):  # mock presenter just raises the error rather than creating dialog
        md.setData(model_index(index), str(value), QtCore.Qt.ItemDataRole.EditRole)


@pytest.mark.parametrize("procedure", PROCEDURES)
def test_set_procedure(model, procedure):
    """Test that changing model procedure correctly changes it in the Controls object."""
    params = copy(fields[procedure])
    params.remove("procedure")

    md = model("calculate")
    md.set_procedure(procedure)

    assert md.presenter.model.controls.procedure == procedure
    assert md.fit_settings == params
