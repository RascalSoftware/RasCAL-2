"""Tests for the Presenter."""

from unittest.mock import MagicMock, patch

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
        self.terminal_widget = MagicMock()
        self.handle_results = MagicMock()
        self.end_run = MagicMock()
        self.logging = MagicMock()


@pytest.fixture
def presenter():
    pr = MainWindowPresenter(MockWindowView())
    pr.model = MagicMock()
    pr.model.controls = Controls()

    return pr


@pytest.mark.parametrize(["param", "value"], [("nSamples", 50), ("calcSldDuringFit", True), ("parallel", "contrasts")])
def test_set_controls_data(presenter, param, value):
    """Check that setting values are correctly propagated to the Controls object."""
    assert presenter.edit_controls(param, value)
    assert getattr(presenter.model.controls, param) == value


@pytest.mark.parametrize(
    ["param", "value"], [("nSamples", "???"), ("calcSldDuringFit", "something"), ("parallel", "bad parallel setting")]
)
def test_controls_validation_error(presenter, param, value):
    """Test that data is not changed if invalid data is passed to set."""
    try:
        presenter.edit_controls(param, value)
    except ValidationError as err:
        with pytest.raises(ValidationError, match=f"{param}"):
            raise err
    else:
        raise AssertionError("Invalid data did not raise error!")


@patch("RATapi.inputs.make_input")
@patch("rascal2.ui.presenter.RATRunner")
def test_run_and_interrupt(mock_runner, mock_inputs, presenter):
    """Test that the runner can be started and interrupted."""
    presenter.run()
    presenter.interrupt_terminal()

    mock_inputs.assert_called_once()
    presenter.runner.start.assert_called_once()
    presenter.runner.interrupt.assert_called_once()


def test_handle_results(presenter):
    """Test that results are handed to the view correctly."""
    presenter.runner = MagicMock()
    presenter.runner.results = "TEST RESULTS"
    presenter.handle_results()

    presenter.view.handle_results.assert_called_once_with("TEST RESULTS")


def test_stop_run(presenter):
    """Test that log info is emitted and the run is stopped when stop_run is called."""
    presenter.handle_interrupt()
    presenter.view.logging.info.assert_called_once_with("RAT run interrupted!")
    presenter.view.end_run.assert_called_once()


def test_run_error(presenter):
    """Test that a critical log is emitted if stop_run is called with an error."""
    presenter.runner = MagicMock()
    presenter.runner.error = ValueError("Test error!")
    presenter.handle_interrupt()
    presenter.view.logging.critical.assert_called_once_with("RAT run failed with exception:\nTest error!")
