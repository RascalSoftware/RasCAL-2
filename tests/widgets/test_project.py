from unittest.mock import MagicMock

import pydantic
import pytest
import RATapi
from PyQt6 import QtCore, QtWidgets
from RATapi.utils.enums import Calculations, Geometries, LayerModels

import rascal2.widgets.delegates as delegates
import rascal2.widgets.inputs as inputs
from rascal2.widgets.project import (
    AbstractProjectTabWidget,
    ClassListModel,
    ParameterFieldWidget,
    ProjectFieldWidget,
    ProjectTabEditWidget,
    ProjectTabViewWidget,
    ProjectWidget,
)


class MockModel(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.project = RATapi.Project()
        self.controls = MagicMock()
        self.project_updated = MagicMock()


class MockPresenter(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = MockModel()
        self.edit_project = MagicMock()


class MockMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.presenter = MockPresenter()


class DataModel(pydantic.BaseModel, validate_assignment=True):
    """A test Pydantic model."""

    name: str = "Test Model"
    value: int = 15


parent = MockMainWindow()


@pytest.fixture
def classlist():
    """A test ClassList."""
    return RATapi.ClassList([DataModel(name="A", value=1), DataModel(name="B", value=6), DataModel(name="C", value=18)])


@pytest.fixture
def table_model(classlist):
    """A test ClassListModel."""
    return ClassListModel(classlist, parent)


@pytest.fixture
def setup_project_widget():
    parent = MockMainWindow()
    project_widget = ProjectWidget(parent)
    project_widget.update_project_view()
    return project_widget


@pytest.fixture
def param_classlist():
    def _classlist(protected_indices):
        return RATapi.ClassList(
            [
                RATapi.models.ProtectedParameter(name=str(i)) if i in protected_indices else RATapi.models.Parameter()
                for i in [0, 1, 2]
            ]
        )

    return _classlist


@pytest.fixture
def param_model(param_classlist):
    def _param_model(protected_indices):
        model = ClassListModel(param_classlist(protected_indices), parent)
        return model

    return _param_model


def test_project_widget_initial_state(setup_project_widget):
    """
    Tests the inital state of the ProjectWidget class.
    """
    project_widget = setup_project_widget

    # Check the layout of the project view
    assert project_widget.stacked_widget.currentIndex() == 0

    assert project_widget.edit_project_button.isEnabled()
    assert project_widget.edit_project_button.text() == "Edit Project"

    assert project_widget.calculation_label.text() == "Calculation:"
    assert project_widget.calculation_type.text() == Calculations.NonPolarised
    assert project_widget.calculation_type.isReadOnly()

    assert project_widget.model_type_label.text() == "Model Type:"
    assert project_widget.model_type.text() == LayerModels.StandardLayers
    assert project_widget.model_type.isReadOnly()

    assert project_widget.geometry_label.text() == "Geometry:"
    assert project_widget.geometry_type.text() == Geometries.AirSubstrate
    assert project_widget.geometry_type.isReadOnly()

    # Check the layout of the edit view
    assert project_widget.save_project_button.isEnabled()
    assert project_widget.save_project_button.text() == "Save Project"

    assert project_widget.cancel_button.isEnabled()
    assert project_widget.cancel_button.text() == "Cancel"

    assert project_widget.edit_calculation_label.text() == "Calculation:"
    assert project_widget.calculation_combobox.currentText() == Calculations.NonPolarised
    for ix, calc in enumerate(Calculations):
        assert project_widget.calculation_combobox.itemText(ix) == calc

    assert project_widget.edit_model_type_label.text() == "Model Type:"
    assert project_widget.model_combobox.currentText() == LayerModels.StandardLayers
    for ix, model in enumerate(LayerModels):
        assert project_widget.model_combobox.itemText(ix) == model

    assert project_widget.edit_geometry_label.text() == "Geometry:"
    assert project_widget.geometry_combobox.currentText() == Geometries.AirSubstrate
    for ix, geometry in enumerate(Geometries):
        assert project_widget.geometry_combobox.itemText(ix) == geometry

    for ix, tab in enumerate(project_widget.tabs):
        assert project_widget.project_tab.tabText(ix) == tab
        assert project_widget.edit_project_tab.tabText(ix) == tab

    assert project_widget.project_tab.currentIndex() == 0
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
    assert project_widget.model_combobox.currentText() == LayerModels.StandardLayers
    assert project_widget.calculation_combobox.currentText() == Calculations.NonPolarised

    project_widget.cancel_button.click()
    assert project_widget.stacked_widget.currentIndex() == 0

    assert project_widget.geometry_type.text() == Geometries.AirSubstrate
    assert project_widget.model_type.text() == LayerModels.StandardLayers
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

    assert project_widget.draft_project["geometry"] == Geometries.SubstrateLiquid
    assert project_widget.draft_project["model"] == LayerModels.CustomXY
    assert project_widget.draft_project["calculation"] == Calculations.Domains

    project_widget.save_changes()
    assert project_widget.parent.presenter.edit_project.call_count == 1


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

    assert project_widget.draft_project["geometry"] == Geometries.SubstrateLiquid
    assert project_widget.draft_project["model"] == LayerModels.CustomXY
    assert project_widget.draft_project["calculation"] == Calculations.Domains

    project_widget.cancel_button.click()
    assert project_widget.parent.presenter.edit_project.call_count == 0

    assert project_widget.calculation_combobox.currentText() == Calculations.NonPolarised
    assert project_widget.calculation_type.text() == Calculations.NonPolarised
    assert project_widget.model_combobox.currentText() == LayerModels.StandardLayers
    assert project_widget.model_type.text() == LayerModels.StandardLayers
    assert project_widget.geometry_combobox.currentText() == Geometries.AirSubstrate
    assert project_widget.geometry_type.text() == Geometries.AirSubstrate


def test_domains_tab(setup_project_widget):
    """
    Tests that domain tab is visible.
    """
    project_widget = setup_project_widget
    project_widget.edit_project_button.click()
    project_widget.calculation_combobox.setCurrentText(Calculations.Domains)
    assert project_widget.draft_project["calculation"] == Calculations.Domains
    project_widget.parent_model.project.calculation = Calculations.Domains
    project_widget.calculation_type.setText(Calculations.Domains)
    project_widget.handle_domains_tab()

    domains_tab_index = 5
    assert project_widget.project_tab.isTabVisible(domains_tab_index)


def test_model_init(table_model, classlist):
    """Test that initialisation works correctly for ClassListModels."""
    model = table_model

    assert model.classlist == classlist
    assert model.item_type == DataModel
    assert model.headers == ["name", "value"]
    assert not model.edit_mode


def test_model_flags(table_model):
    """Test that model flags are as expected."""
    model = table_model

    # PyQt item flags are bitwise-encoded, so we test for inclusion with the & operator
    for row in [0, 1, 2]:
        assert not model.flags(model.index(row, 1)) & QtCore.Qt.ItemFlag.ItemIsEditable
        assert model.flags(model.index(row, 2)) & QtCore.Qt.ItemFlag.ItemIsEditable

    model.edit_mode = True

    for row in [0, 1, 2]:
        for column in [1, 2]:
            assert model.flags(model.index(row, column)) & QtCore.Qt.ItemFlag.ItemIsEditable


def test_model_layout_data(table_model):
    """Test that the model layout and data is as expected."""
    model = table_model

    assert model.rowCount() == 3
    assert model.columnCount() == 3

    expected_data = [["", "A", 1], ["", "B", 6], ["", "C", 18]]
    headers = [None, "name", "value"]

    for row in [0, 1, 2]:
        for column in [0, 1, 2]:
            assert model.data(model.index(row, column)) == expected_data[row][column]

    for column in [0, 1, 2]:
        assert model.headerData(column, QtCore.Qt.Orientation.Horizontal) == headers[column]


def test_model_set_data(table_model):
    """Test that data can be set successfully, but is thrown out if it breaks the Pydantic model rules."""
    model = table_model

    assert model.setData(model.index(1, 2), 4)
    assert model.classlist[1].value == 4

    assert model.setData(model.index(1, 1), "D")
    assert model.classlist[1].name == "D"

    assert not model.setData(model.index(2, 2), 19.4)
    assert model.classlist[2].value == 18


def test_append(table_model):
    """Test that append_item successfully adds an item of the relevant type."""
    model = table_model

    model.append_item()

    assert len(model.classlist) == 4
    assert model.classlist[-1].name == "Test Model"
    assert model.classlist[-1].value == 15


def test_delete(table_model):
    """Test that delete_item deletes the item at the desired index."""
    model = table_model

    model.delete_item(1)

    assert len(model.classlist) == 2
    assert [m.name for m in model.classlist] == ["A", "C"]
    assert [m.value for m in model.classlist] == [1, 18]


def test_project_field_init():
    """Test that the ProjectFieldWidget is initialised correctly."""
    widget = ProjectFieldWidget(parent)

    assert widget.table.model() is None
    assert widget.add_button.isHidden()


def test_project_field_update_model(classlist):
    """Test that the correct changes are made when the model is updated in the ProjectFieldWidget."""
    widget = ProjectFieldWidget(parent)
    widget.update_model(classlist)

    assert widget.table.isColumnHidden(0)

    assert widget.model.classlist == classlist
    assert isinstance(
        widget.table.itemDelegateForColumn(1).createEditor(None, None, widget.model.index(1, 1)),
        inputs.BaseInputWidget,
    )
    assert isinstance(
        widget.table.itemDelegateForColumn(2).createEditor(None, None, widget.model.index(1, 2)),
        inputs.IntInputWidget,
    )

    for row in [0, 1, 2]:
        assert not widget.table.isPersistentEditorOpen(widget.model.index(row, 1))
        assert widget.table.isPersistentEditorOpen(widget.model.index(row, 2))


def test_edit_mode(classlist):
    """Test that edit mode makes the expected changes."""
    widget = ProjectFieldWidget(parent)
    widget.update_model(classlist)
    widget.edit()

    assert widget.model.edit_mode
    assert not widget.add_button.isHidden()
    assert not widget.table.isColumnHidden(0)

    for row in [0, 1, 2]:
        assert isinstance(widget.table.indexWidget(widget.model.index(row, 0)), QtWidgets.QPushButton)
        for column in [1, 2]:
            assert widget.table.isPersistentEditorOpen(widget.model.index(row, column))


def test_delete_button(classlist):
    """Test that delete buttons work as expected."""
    widget = ProjectFieldWidget(parent)
    widget.update_model(classlist)

    delete_button = widget.make_delete_button(1)
    delete_button.click()

    assert len(widget.model.classlist) == 2
    assert [m.name for m in widget.model.classlist] == ["A", "C"]
    assert [m.value for m in widget.model.classlist] == [1, 18]


@pytest.mark.parametrize("protected", ([], [0, 2], [1]))
def test_model_protected_parameters(param_model, protected):
    """Test that protected parameters are successfully recorded and flagged."""
    model = param_model(protected)

    assert model.protected_indices == protected

    model.edit_mode = True

    for row in [0, 1, 2]:
        for column in [1, 2]:
            if row in protected and column == 1:
                assert not model.flags(model.index(row, column)) & QtCore.Qt.ItemFlag.ItemIsEditable
            else:
                assert model.flags(model.index(row, column)) & QtCore.Qt.ItemFlag.ItemIsEditable


def test_param_item_delegates(param_classlist):
    """Test that parameter models have the expected item delegates."""
    widget = ParameterFieldWidget(parent)
    widget.parent = MagicMock()
    widget.update_model(param_classlist([]))

    for column, header in enumerate(widget.model.headers, start=1):
        if header in ["min", "value", "max"]:
            assert isinstance(widget.table.itemDelegateForColumn(column), delegates.ValueSpinBoxDelegate)
        else:
            assert isinstance(widget.table.itemDelegateForColumn(column), delegates.ValidatedInputDelegate)


def test_hidden_bayesian_columns(param_classlist):
    """Test that Bayes columns are hidden when procedure is not Bayesian."""
    widget = ParameterFieldWidget(parent)
    widget.parent = MagicMock()
    mock_controls = widget.parent.parent.parent_model.controls = MagicMock()
    mock_controls.procedure = "calculate"
    bayesian_columns = ["prior_type", "mu", "sigma"]

    widget.update_model(param_classlist([]))

    for item in bayesian_columns:
        index = widget.model.headers.index(item)
        assert widget.table.isColumnHidden(index + 1)

    mock_controls.procedure = "dream"
    widget.update_model(param_classlist([]))

    for item in bayesian_columns:
        index = widget.model.headers.index(item)
        assert not widget.table.isColumnHidden(index + 1)


def test_project_tab_init():
    """Test that the project tab correctly creates field widgets."""
    fields = ["my_field", "parameters", "bulk_in"]

    tab = AbstractProjectTabWidget(fields, parent)
    layout = tab.layout().itemAt(0).widget().widget().layout()

    for item, expected_header in zip([0, 2, 4], ["My Field", "Parameters", "Bulk In"]):
        widget = layout.itemAt(item).widget()
        assert isinstance(widget, QtWidgets.QLabel)
        assert widget.text() == expected_header

    for field in fields:
        if field in RATapi.project.parameter_class_lists:
            assert isinstance(tab.tables[field], ParameterFieldWidget)
        else:
            assert isinstance(tab.tables[field], ProjectFieldWidget)


def test_project_tab_edit_update_model(classlist, param_classlist):
    """Test that updating a ProjectTabEditWidget produces the desired models."""

    new_model = {"my_field": classlist, "parameters": param_classlist([])}

    tab = ProjectTabEditWidget(list(new_model), parent)
    # change the parent to a mock to avoid spec issues
    for table in tab.tables.values():
        table.parent = MagicMock()
    tab.update_model(new_model)

    for field in new_model:
        assert tab.tables[field].model.classlist == new_model[field]
        assert tab.tables[field].model.edit_mode


def test_project_tab_view_update_model():
    """Test that updating a ProjectTabViewWidget produces the desired models."""

    project = RATapi.Project()
    tab = ProjectTabViewWidget(["parameters", "bulk_in", "backgrounds"], parent)
    for table in tab.tables.values():
        table.parent = MagicMock()
    tab.update_model(project)

    for field in tab.tables:
        assert tab.tables[field].model.classlist == getattr(project, field)
