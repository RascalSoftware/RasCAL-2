"""Tests for the undo Command classes."""

from unittest.mock import MagicMock, patch

import pytest
from ratapi import Controls, Project
from ratapi.rat_core import ProblemDefinition

from rascal2.core.commands import CommandID, EditControls, EditProject, SaveCalculationOutputs
from rascal2.ui.presenter import MainWindowPresenter


@pytest.fixture
def presenter(mock_window_view):
    with (
        patch("rascal2.ui.presenter.LOGGER", autospec=True),
        patch("rascal2.ui.model.os.chdir", autospec=True),
    ):
        pr = MainWindowPresenter(mock_window_view)
        results = MagicMock()
        results.calculationResults.sumChi = 45
        pr.quick_run = MagicMock(return_value=results)
        pr.model.controls = Controls()
        pr.model.project = Project()
        pr.model.results = None
        pr.model.result_log = ""

        yield pr


def test_edit_controls(presenter):
    command = EditControls({"procedure": "de", "targetValue": 3}, presenter)
    assert command.id() == CommandID.EditControls
    assert presenter.model.controls.procedure == "calculate"
    assert presenter.model.controls.targetValue == 1
    command.redo()
    assert presenter.model.controls.procedure == "de"
    assert presenter.model.controls.targetValue == 3
    command.undo()
    assert presenter.model.controls.procedure == "calculate"
    assert presenter.model.controls.targetValue == 1


def test_edit_project(presenter):
    command = EditProject({"model": "custom layers"}, presenter)
    assert command.id() == CommandID.EditProject
    assert presenter.model.project.model == "standard layers"
    command.redo()
    assert presenter.model.project.model == "custom layers"
    command.undo()
    assert presenter.model.project.model == "standard layers"


def test_edit_project_preview(presenter):
    command = EditProject({"model": "custom layers"}, presenter, preview=True)
    command.redo()
    presenter.quick_run.assert_called_once()
    assert presenter.model.results.calculationResults.sumChi == 45
    command.undo()
    assert presenter.model.results is None
    command.redo()
    # confirm quick_run is always done once
    presenter.quick_run.assert_called_once()
    assert presenter.model.results.calculationResults.sumChi == 45

    presenter.quick_run.side_effect = ValueError("calculate error")
    command = EditProject({"model": "custom layers"}, presenter, preview=True)
    command.redo()
    # run failed so result is None
    assert command.new_result is None


def test_save_calculation_outputs(presenter):
    project = ProblemDefinition()
    project.params = [4.5]
    results = MagicMock()
    results.calculationResults.sumChi = 45
    log = "Stuff happened during calculation"
    command = SaveCalculationOutputs(project, results, log, presenter)
    assert presenter.model.project.parameters[0].value == 3
    assert presenter.model.results is None
    assert presenter.model.result_log == ""
    command.redo()
    assert presenter.model.project.parameters[0].value == 4.5
    assert presenter.model.results.calculationResults.sumChi == 45
    assert presenter.model.result_log == log
    command.undo()
    assert presenter.model.project.parameters[0].value == 3
    assert presenter.model.results is None
    assert presenter.model.result_log == ""
