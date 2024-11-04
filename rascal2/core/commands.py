"""File for Qt commands."""

import copy
from enum import IntEnum, unique
from typing import Callable

import RATapi
from PyQt6 import QtGui
from RATapi import ClassList


@unique
class CommandID(IntEnum):
    """Unique ID for undoable commands"""

    EditControls = 1000
    EditProject = 2000


class AbstractModelEdit(QtGui.QUndoCommand):
    """Command for editing an attribute of the model."""

    attribute = None

    def __init__(self, new_values: dict, presenter):
        super().__init__()
        self.presenter = presenter
        self.new_values = new_values
        if self.attribute is None:
            raise NotImplementedError("AbstractEditModel should not be instantiated directly.")
        else:
            self.model_class = getattr(self.presenter.model, self.attribute)
        self.old_values = {attr: getattr(self.model_class, attr) for attr in self.new_values}
        self.update_text()

    def update_text(self):
        """Update the undo command text."""
        if len(self.new_values) == 1:
            attr, value = list(self.new_values.items())[0]
            if isinstance(list(self.new_values.values())[0], ClassList):
                text = f"Changed values in {attr}"
            else:
                text = f"Set {self.attribute} {attr} to {value}"
        else:
            text = f"Save update to {self.attribute}"

        self.setText(text)

    @property
    def update_attribute(self) -> Callable:
        """Return the method used to update the attribute."""
        raise NotImplementedError

    def undo(self):
        self.update_attribute(self.old_values)

    def redo(self):
        self.update_attribute(self.new_values)

    def mergeWith(self, command):
        """Merges consecutive Edit controls commands if the attributes are the
        same."""

        # We should think about if merging all Edit controls irrespective of
        # attribute is the way to go for UX
        if list(self.new_values.keys()) != list(command.new_values.keys()):
            return False

        if list(self.old_values.values()) == list(command.new_values.values()):
            self.setObsolete(True)

        self.new_values = command.new_values
        self.update_text()
        return True

    def id(self):
        """Returns ID used for merging commands"""
        raise NotImplementedError


class EditControls(AbstractModelEdit):
    attribute = "controls"

    @property
    def update_attribute(self):
        return self.presenter.model.update_controls

    def id(self):
        return CommandID.EditControls


class EditProject(AbstractModelEdit):
    attribute = "project"

    @property
    def update_attribute(self):
        return self.presenter.model.update_project

    def id(self):
        return CommandID.EditProject


class SaveResults(QtGui.QUndoCommand):
    """Command for saving the Results object.

    Parameters
    ----------
    problem : RATapi.rat_core.ProblemDefinition
        The problem
    results : Union[RATapi.outputs.Results, RATapi.outputs.BayesResults]
        The calculation results.
    log : str
        log text from the given calculation.
    """

    def __init__(self, problem, results, log: str, presenter):
        super().__init__()
        self.presenter = presenter
        self.results = results
        self.log = log
        self.problem = self.get_parameter_values(problem)
        self.old_problem = self.get_parameter_values(RATapi.inputs.make_problem(self.presenter.model.project))
        self.old_results = copy.deepcopy(self.presenter.model.results)
        self.old_log = self.presenter.model.result_log
        self.setText("Save calculation results")

    def get_parameter_values(self, problem_definition: RATapi.rat_core.ProblemDefinition):
        """Get parameter values from problem definition."""
        parameter_field = {
            "parameters": "params",
            "bulk_in": "bulkIn",
            "bulk_out": "bulkOut",
            "scalefactors": "scalefactors",
            "domain_ratios": "domainRatio",
            "background_parameters": "backgroundParams",
            "resolution_parameters": "resolutionParams",
        }

        values = {}
        for class_list in RATapi.project.parameter_class_lists:
            entry = values.setdefault(class_list, [])
            entry.extend(getattr(problem_definition, parameter_field[class_list]))
        return values

    def set_parameter_values(self, values):
        """Update the project given a set of results."""

        for key, value in values.items():
            for index in range(len(value)):
                getattr(self.presenter.model.project, key)[index].value = value[index]
        return values

    def undo(self):
        self.swap_results(self.old_problem, self.old_results, self.old_log)

    def redo(self):
        self.swap_results(self.problem, self.results, self.log)

    def swap_results(self, problem, results, log):
        """Swap problem, result and log in model with given one

        Parameters
        ----------
        problem : RATapi.rat_core.ProblemDefinition
            The problem definition
        results : Union[RATapi.outputs.Results, RATapi.outputs.BayesResults]
            The calculation results.
        log : str
            log text from the given calculation.
        """
        self.set_parameter_values(problem)
        self.presenter.model.update_results(copy.deepcopy(results))
        self.presenter.model.result_log = log
        chi_text = "" if results is None else f"{results.calculationResults.sumChi:.6g}"
        self.presenter.view.controls_widget.chi_squared.setText(chi_text)
        self.presenter.view.terminal_widget.clear()
        self.presenter.view.terminal_widget.write(log)
