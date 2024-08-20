"""Test the Controls widget."""

import pytest
from pydantic.fields import FieldInfo
from PyQt6 import QtWidgets
from RATapi.controls import fields

from rascal2.widgets.controls.view import ControlsWidget, FitSettingsWidget
from tests.controls.control_mocks import MockWindowView


class MockValidationError:
    """A mock of a ValidationError list."""

    def errors(self):
        return [{"msg": "Validation error!"}]


class MockFitSettingsModel:
    def __init__(self, presenter, dataset=None):
        if dataset is None:
            dataset = {"setting 1": "data 1", "setting 2": "data 2", "setting 3": "data 3"}
        dataset["resampleParams"] = "REMOVE WHEN resampleParams IS FIXED"
        self.fit_settings = dataset
        self.model_fields = {s: FieldInfo(annotation=type(dataset[s])) for s in self.fit_settings}
        self.presenter = presenter
        self.allow_setting = True  # for testing setData rejection
        self.last_validation_error = MockValidationError()

    def data(self, setting):
        return self.fit_settings[setting]

    def setData(self, setting, value):
        if self.allow_setting:
            self.fit_settings[setting] = value
            return True
        return False

    def get_procedure_settings(self, procedure):
        return list(self.fit_settings.keys())


view = MockWindowView()


@pytest.fixture
def controls_widget() -> ControlsWidget:
    def _widget():
        widget = ControlsWidget(view)
        return widget

    return _widget


@pytest.fixture
def fit_settings_widget() -> FitSettingsWidget:
    def _widget(data=None):
        widget = FitSettingsWidget(view, "", MockFitSettingsModel(data))
        return widget

    return _widget


def test_toggle_fit(controls_widget):
    """Test that fit settings are hidden when the button is toggled."""
    wg = controls_widget()
    assert wg.fit_settings.isVisibleTo(wg)
    wg.fit_settings_button.toggle()
    assert not wg.fit_settings.isVisibleTo(wg)
    wg.fit_settings_button.toggle()
    assert wg.fit_settings.isVisibleTo(wg)


def test_toggle_run_disables(controls_widget):
    """Assert that Controls settings are disabled and Stop button enabled when the run button is pressed."""
    wg = controls_widget()
    assert wg.fit_settings.isEnabled()
    assert wg.procedure_dropdown.isEnabled()
    assert not wg.stop_button.isEnabled()
    wg.run_button.toggle()
    assert not wg.fit_settings.isEnabled()
    assert not wg.procedure_dropdown.isEnabled()
    assert wg.stop_button.isEnabled()
    wg.run_button.toggle()
    assert wg.fit_settings.isEnabled()
    assert wg.procedure_dropdown.isEnabled()
    assert not wg.stop_button.isEnabled()


def test_stop_button_interrupts(controls_widget):
    """Test that an interrupt signal is sent to the presenter when Stop is pressed."""
    wg = controls_widget()
    wg.run_button.toggle()
    wg.stop_button.click()
    assert wg.presenter.terminal_interrupted


@pytest.mark.parametrize("procedure", ["calculate", "simplex", "de", "ns", "dream"])
def test_procedure_select(controls_widget, procedure):
    """Test that the procedure selector correctly changes the widget."""
    wg = controls_widget()
    wg.procedure_dropdown.setCurrentText(procedure)
    current_fit_set = wg.fit_settings_layout.currentWidget()
    for setting in fields[procedure]:
        if setting not in ["procedure", "resampleParams"]:
            assert setting in list(current_fit_set.rows.keys())


def test_create_fit_settings(fit_settings_widget):
    """Test that fit settings are correctly created from the model's dataset."""
    wg = fit_settings_widget()
    grid = wg.widget().layout()
    for i in [1, 2, 3]:
        assert grid.itemAtPosition(2 * (i - 1), 0).widget().text() == f"setting {i}"
        assert grid.itemAtPosition(2 * (i - 1), 1).widget().get_data() == f"data {i}"


def test_invalid_input(fit_settings_widget):
    """Test that invalid inputs are propagated correctly."""
    wg = fit_settings_widget()
    wg.model.allow_setting = False
    grid = wg.widget().layout()
    entry = grid.itemAtPosition(0, 1).widget()

    entry.set_data("bad data")

    validation_box = grid.itemAtPosition(1, 1).widget()
    assert validation_box.text() == "Validation error!"


@pytest.mark.parametrize("entries", [(1, 3), [2], (1, 2), (1, 2, 3)])
def test_invalid_data_run(controls_widget, fit_settings_widget, entries):
    """Tests that the widget refuses to run if values have invalid data."""
    wg = controls_widget()
    fit_tab = fit_settings_widget()
    fit_lay = QtWidgets.QStackedLayout()
    fit_lay.addWidget(fit_tab)
    fit_wg = QtWidgets.QWidget()
    fit_wg.setLayout(fit_lay)

    wg.fit_settings_layout = fit_lay
    wg.fit_settings = fit_wg

    fit_tab.model.allow_setting = False
    grid = fit_tab.widget().layout()
    for entry in entries:
        entry = grid.itemAtPosition(2 * (entry - 1), 1).widget()
        entry.set_data("bad data")

    for entry in entries:
        assert f"setting {entry}" in fit_tab.get_invalid_inputs()

    wg.run_button.toggle()
    assert not wg.stop_button.isEnabled()  # to assert run hasn't started
    for entry in entries:
        assert f"setting {entry}" in wg.validation_label.text()
