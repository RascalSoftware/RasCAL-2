"""Test the Controls widget."""

import pytest
from PyQt6 import QtWidgets
from RATapi.controls import Controls, fields

from rascal2.widgets.controls import ControlsWidget, FitSettingsWidget


class MockValidationError:
    """A mock of a ValidationError list."""

    def errors(self):
        return [{"msg": "Validation error!"}]


class MockModel:
    """A mock Model."""

    def __init__(self):
        self.controls = Controls()


class MockPresenter:
    """A mock MainWindowPresenter class."""

    def __init__(self):
        self.model = MockModel()
        self.controls = self.model.controls
        self.allow_setting = True
        self.terminal_interrupted = False

    def getControlsAttribute(self, attr):
        return getattr(self.controls, attr)

    def editControls(self, setting, value):
        if self.allow_setting:
            setattr(self.controls, setting, value)
            return True
        self.last_validation_error = MockValidationError()
        return False

    def interrupt_terminal(self):
        self.terminal_interrupted = True


class MockWindowView(QtWidgets.QMainWindow):
    """A mock MainWindowView class."""

    def __init__(self):
        super().__init__()
        self.presenter = MockPresenter()


view = MockWindowView()


@pytest.fixture
def controls_widget() -> ControlsWidget:
    def _widget():
        widget = ControlsWidget(view)
        return widget

    return _widget


@pytest.fixture
def fit_settings_widget() -> FitSettingsWidget:
    def _widget(procedure):
        widget = FitSettingsWidget(view, procedure, MockPresenter())
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
    wg = fit_settings_widget("calculate")
    grid = wg.layout().itemAt(0).widget().widget().layout()
    for i, setting in enumerate(["parallel", "calcSldDuringFit", "display"]):
        assert grid.itemAtPosition(2 * i, 0).widget().text() == setting
        assert grid.itemAtPosition(2 * i, 1).widget().get_data() == getattr(wg.presenter.model.controls, setting)


def test_invalid_input(fit_settings_widget):
    """Test that invalid inputs are propagated correctly."""
    wg = fit_settings_widget("dream")
    wg.presenter.allow_setting = False
    grid = wg.layout().itemAt(0).widget().widget().layout()
    entry = grid.itemAtPosition(10, 1).widget()

    entry.set_data(0)
    entry.editor.editingFinished.emit()

    validation_box = grid.itemAtPosition(11, 1).widget()
    assert validation_box.text() == "Validation error!"


@pytest.mark.parametrize(("procedure", "bad_entries"), [("ns", [10]), ("ns", [10, 12]), ("dream", [10, 12])])
def test_invalid_data_run(controls_widget, fit_settings_widget, procedure, bad_entries):
    """Tests that the widget refuses to run if values have invalid data."""
    wg = controls_widget()
    fit_tab = fit_settings_widget("dream")
    fit_lay = QtWidgets.QStackedLayout()
    fit_lay.addWidget(fit_tab)
    fit_wg = QtWidgets.QWidget()
    fit_wg.setLayout(fit_lay)

    wg.fit_settings_layout = fit_lay
    wg.fit_settings = fit_wg

    fit_tab.presenter.allow_setting = False
    grid = fit_tab.layout().itemAt(0).widget().widget().layout()
    for entry in bad_entries:
        entry = grid.itemAtPosition(entry, 1).widget()
        entry.set_data(0)
        entry.editor.editingFinished.emit()

    entry_names = [grid.itemAtPosition(entry, 0).widget().text() for entry in bad_entries]
    for entry_name in entry_names:
        assert entry_name in fit_tab.get_invalid_inputs()

    wg.run_button.toggle()
    assert not wg.stop_button.isEnabled()  # to assert run hasn't started
    for entry_name in entry_names:
        assert entry_name in wg.validation_label.text()
