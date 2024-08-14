"""Test the Controls widget."""

from enum import StrEnum

import pytest
from PyQt6 import QtCore, QtWidgets

from rascal2.widgets import ControlsWidget
from rascal2.widgets.delegates import BoolDelegate, EnumDelegate
from tests.controls.control_mocks import MockPresenter


class MockTableModel(QtCore.QAbstractTableModel):
    def __init__(self, presenter, dataset):
        super().__init__()
        if dataset is None:
            dataset = ["data 1", "data 2", "data 3"]
        self.fit_settings = dataset
        self.headers = [f"Header {i}" for i in range(0, len(dataset))]
        self.presenter = presenter
        self.procedure = "fry eggs"

    def columnCount(self, parent=None):
        return 1

    def rowCount(self, parent=None):
        return 5

    def headerData(self, section, orientation, role):
        return self.headers[section]

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        return str(self.fit_settings[index.row()])

    def setData(self, index, value, role):
        self.data[index.row()] = value
        return True

    def set_procedure(self, procedure):
        self.procedure = procedure
        self.datatypes = [type(f) for f in self.fit_settings]


# can't call this "TestEnum" or pytest tries to collect it as a test class
class MyEnum(StrEnum):
    val_1 = "value 1"
    val_2 = "value 2"
    val_3 = "value 3"


@pytest.fixture
def widget():
    def _widget(data=None):
        widget = ControlsWidget(MockPresenter("calculate"))
        widget.fit_settings_model = MockTableModel(widget.presenter, data)
        widget.set_procedure("fry eggs")  # reset procedure to setup mock table model
        return widget

    return _widget


@pytest.mark.parametrize(
    "data", [[1, 3, 5], [13.0, False, True, True, 6], [True, MyEnum("value 2"), 55.0, MyEnum("value 1")]]
)
def test_delegate_types(widget, data):
    """Test that the correct delegate types are given to each entry in the table."""
    wg = widget(data)
    for i in range(0, len(data)):
        if isinstance(data[i], bool):
            delegate = BoolDelegate
        elif isinstance(data[i], StrEnum):
            delegate = EnumDelegate
        else:
            delegate = QtWidgets.QStyledItemDelegate

        assert isinstance(wg.fit_settings.itemDelegateForRow(i), delegate)


def test_toggle_fit(widget):
    """Test that fit settings are hidden when the button is toggled."""
    wg = widget()
    assert wg.fit_settings.isVisibleTo(wg)
    wg.fit_settings_button.toggle()
    assert not wg.fit_settings.isVisibleTo(wg)
    wg.fit_settings_button.toggle()
    assert wg.fit_settings.isVisibleTo(wg)


def test_toggle_run_disables(widget):
    """Assert that Controls settings are disabled when the run button is pressed."""
    wg = widget()
    assert wg.fit_settings.isEnabled()
    assert wg.procedure_dropdown.isEnabled()
    wg.run_button.toggle()
    assert not wg.fit_settings.isEnabled()
    assert not wg.procedure_dropdown.isEnabled()
    wg.run_button.toggle()
    assert wg.fit_settings.isEnabled()
    assert wg.procedure_dropdown.isEnabled()
