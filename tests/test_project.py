from unittest.mock import MagicMock

import pytest
from PyQt6 import QtCore, QtWidgets
from RATapi.utils.enums import Calculations, Geometries, LayerModels

from rascal2.widgets.project import ProjectWidget


class MockModel(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.project = MagicMock()
        self.project.calculation = Calculations.NonPolarised
        self.project.model = LayerModels.CustomLayers
        self.project.geometry = Geometries.AirSubstrate


class MockPresenter(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = MockModel()
        self.edit_project = MagicMock()


class MockMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.presenter = MockPresenter()


@pytest.fixture
def setup_project_widget():
    parent = MockMainWindow()
    project_widget = ProjectWidget(parent)
    return project_widget


def test_project_widget_initial_state(setup_project_widget):
    """
    Tests the inital state of the ProjectWidget class.
    """
    project_widget = setup_project_widget

    assert project_widget.undo_stack.isClean()

    # Check the layout of the project view
    assert project_widget.stacked_widget.currentIndex() == 0

    assert project_widget.edit_project_button.isEnabled()
    assert project_widget.edit_project_button.text() == " Edit Project"

    assert project_widget.calculation_label.text() == "Calculation:"
    assert project_widget.calculation_type.text() == Calculations.NonPolarised
    assert project_widget.calculation_type.isReadOnly()

    assert project_widget.model_type_label.text() == "Model Type:"
    assert project_widget.model_type.text() == LayerModels.CustomLayers
    assert project_widget.model_type.isReadOnly()

    assert project_widget.geometry_label.text() == "Geometry:"
    assert project_widget.geometry_type.text() == Geometries.AirSubstrate
    assert project_widget.geometry_type.isReadOnly()

    for ix, tab in enumerate(["Parameters", "Experimental Parameters", "Layers", "Data", "Contrasts"]):
        assert project_widget.project_tab.tabText(ix) == tab

    assert project_widget.project_tab.currentIndex() == 0

    # Check the layout of the edit view
    assert project_widget.save_project_button.isEnabled()
    assert project_widget.save_project_button.text() == " Save Project"

    assert project_widget.cancel_button.isEnabled()
    assert project_widget.cancel_button.text() == " Cancel"

    assert project_widget.edit_calculation_label.text() == "Calculation:"
    assert project_widget.calculation_combobox.count() == len(Calculations)
    assert project_widget.calculation_combobox.currentText() == Calculations.NonPolarised
    for ix, calc in zip(range(project_widget.calculation_combobox.count()), Calculations):
        assert project_widget.calculation_combobox.itemText(ix) == calc

    assert project_widget.edit_model_type_label.text() == "Model Type:"
    assert project_widget.model_combobox.count() == len(LayerModels)
    assert project_widget.model_combobox.currentText() == LayerModels.CustomLayers
    for ix, model in zip(range(project_widget.model_combobox.count()), LayerModels):
        assert project_widget.model_combobox.itemText(ix) == model

    assert project_widget.edit_geometry_label.text() == "Geometry:"
    assert project_widget.geometry_combobox.count() == len(Geometries)
    assert project_widget.geometry_combobox.currentText() == Geometries.AirSubstrate
    for ix, geometry in zip(range(project_widget.geometry_combobox.count()), Geometries):
        assert project_widget.geometry_combobox.itemText(ix) == geometry

    for ix, tab in enumerate(["Parameters", "Experimental Parameters", "Layers", "Data", "Contrasts"]):
        assert project_widget.edit_project_tab.tabText(ix) == tab

    assert project_widget.edit_project_tab.currentIndex() == 0


def test_edit_cancel_button_toggle(setup_project_widget):
    """
    Tests clicking the edit button cuases the stacked widget to change state.
    """
    project_widget = setup_project_widget

    assert project_widget.stacked_widget.currentIndex() == 0
    project_widget.edit_project_button.click()
    assert project_widget.stacked_widget.currentIndex() == 1

    assert project_widget.geometry_combobox.currentText() == Geometries.AirSubstrate
    assert project_widget.model_combobox.currentText() == LayerModels.CustomLayers
    assert project_widget.calculation_combobox.currentText() == Calculations.NonPolarised

    project_widget.cancel_button.click()
    assert project_widget.stacked_widget.currentIndex() == 0

    assert project_widget.geometry_type.text() == Geometries.AirSubstrate
    assert project_widget.model_type.text() == LayerModels.CustomLayers
    assert project_widget.calculation_type.text() == Calculations.NonPolarised


def test_save_changes_to_model_project(setup_project_widget):
    """
    Tests that making changes to the project settings
    """
    project_widget = setup_project_widget

    project_widget.edit_project_button.click()

    project_widget.calculation_combobox.setCurrentText(Calculations.Domains)
    project_widget.geometry_combobox.setCurrentText(Geometries.SubstrateLiquid)
    project_widget.model_combobox.setCurrentText(LayerModels.CustomXY)
    assert len(project_widget.undo_stack) == 3

    project_widget.save_project_button.click()
    assert project_widget.undo_stack.isClean()
    assert project_widget.presenter.edit_project.call_count == 1


def test_cancel_changes_to_model_project(setup_project_widget):
    """
    Tests that making changes to the project settings and
    not saving them reverts the changes.
    """
    project_widget = setup_project_widget

    project_widget.edit_project_button.click()

    project_widget.calculation_combobox.setCurrentText(Calculations.Domains)
    project_widget.geometry_combobox.setCurrentText(Geometries.SubstrateLiquid)
    project_widget.model_combobox.setCurrentText(LayerModels.CustomXY)
    assert len(project_widget.undo_stack) == 3
    project_widget.cancel_button.click()
    assert project_widget.presenter.edit_project.call_count == 0

    assert project_widget.calculation_combobox.currentText() == Calculations.NonPolarised
    assert project_widget.calculation_type.text() == Calculations.NonPolarised
    assert project_widget.model_combobox.currentText() == LayerModels.CustomLayers
    assert project_widget.model_type.text() == LayerModels.CustomLayers
    assert project_widget.geometry_combobox.currentText() == Geometries.AirSubstrate
    assert project_widget.geometry_type.text() == Geometries.AirSubstrate

    assert project_widget.undo_stack.isClean()


def test_domains_tab(setup_project_widget):
    """
    Tests that domain tab is visible.
    """
    project_widget = setup_project_widget
    project_widget.edit_project_button.click()
    project_widget.calculation_combobox.setCurrentText(Calculations.Domains)
    project_widget.presenter.model.project.calculation = Calculations.Domains
    project_widget.calculation_type.setText(Calculations.Domains)
    assert len(project_widget.undo_stack) == 1
    project_widget.save_project_button.click()
    assert project_widget.undo_stack.isClean()

    for ix, tab in enumerate(["Parameters", "Experimental Parameters", "Layers", "Data", "Contrasts", "Domains"]):
        assert project_widget.project_tab.tabText(ix) == tab

    assert project_widget.project_tab.currentIndex() == 0
    project_widget.edit_project_button.click()

    for ix, tab in enumerate(["Parameters", "Experimental Parameters", "Layers", "Data", "Contrasts", "Domains"]):
        assert project_widget.edit_project_tab.tabText(ix) == tab

    assert project_widget.edit_project_tab.currentIndex() == 0
