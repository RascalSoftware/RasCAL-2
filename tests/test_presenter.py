"""Tests for the Presenter."""

import pytest
from pydantic import ValidationError
from PyQt6 import QtWidgets
from RATapi import Controls

from rascal2.ui.presenter import MainWindowPresenter


class MockUndoStack:
    """A mock Undo stack."""

    def __init__(self):
        self.stack = []

    def push(self, command):
        command.redo()


class MockWindowView(QtWidgets.QMainWindow):
    """A mock MainWindowView class."""

    def __init__(self):
        super().__init__()
        self.undo_stack = MockUndoStack()


class MockModel:
    """A mock Model."""

    def __init__(self):
        self.controls = Controls()


@pytest.fixture
def presenter():
    pr = MainWindowPresenter(MockWindowView())
    pr.model = MockModel()
    return pr


def test_get_controls_data(presenter):
    """Test that the Controls data is correctly retrieved."""
    fields = presenter.getControlsAttribute("model_fields").keys()
    values = [getattr(presenter.model.controls, field) for field in fields]
    assert [presenter.getControlsAttribute(field) for field in fields] == values


@pytest.mark.parametrize(["param", "value"], [("nSamples", 50), ("calcSldDuringFit", True), ("parallel", "contrasts")])
def test_set_controls_data(presenter, param, value):
    """Check that setting values are correctly propagated to the Controls object."""
    assert presenter.editControls(param, value)
    assert getattr(presenter.model.controls, param) == value


@pytest.mark.parametrize(
    ["param", "value"], [("nSamples", "???"), ("calcSldDuringFit", "something"), ("parallel", "bad parallel setting")]
)
def test_controls_validation_error(presenter, param, value):
    """Test that data is not changed if invalid data is passed to set."""
    assert presenter.editControls(param, value) is False
    with pytest.raises(ValidationError, match=f"{param}"):
        raise presenter.last_validation_error
