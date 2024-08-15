"""Widget for setting up the Controls class."""

from enum import Enum
from typing import Callable

from pydantic.fields import FieldInfo
from PyQt6 import QtCore, QtGui, QtWidgets
from RATapi.utils.enums import Procedures

from rascal2.config import path_for
from rascal2.widgets.controls.model import FitSettingsModel


class ControlsWidget(QtWidgets.QWidget):
    """Widget for editing the Controls object."""

    def __init__(self, presenter):
        super().__init__()
        self.presenter = presenter

        # create fit settings view and setup connection to model
        fit_settings_model = FitSettingsModel(self.presenter)
        self.fit_settings_layout = QtWidgets.QStackedLayout()
        for procedure in Procedures:
            fit_set = FitSettingsWidget(self, procedure, fit_settings_model)
            self.fit_settings_layout.addWidget(fit_set)

        fit_settings_widget = QtWidgets.QWidget()
        fit_settings_widget.setLayout(self.fit_settings_layout)
        self.fit_settings = QtWidgets.QScrollArea()
        self.fit_settings.setWidget(fit_settings_widget)

        # set initial procedure to whatever is in the Controls object
        init_procedure = [p.value for p in Procedures].index(self.presenter.model.controls.procedure)
        self.set_procedure(init_procedure)

        # create run button
        self.play_icon = QtGui.QIcon(path_for("play.png"))
        self.stop_icon = QtGui.QIcon(path_for("stop.png"))
        self.run_button = QtWidgets.QPushButton(icon=self.play_icon, text="Run")
        self.run_button.setStyleSheet("background-color: green;")
        self.run_button.setCheckable(True)
        self.run_button.toggled.connect(self.toggle_run_button)

        # create box containing chi-squared value
        chi_box = QtWidgets.QHBoxLayout()
        self.chi_squared = QtWidgets.QLineEdit("1.060")  # TODO hook this up when we can actually run... issue #9
        self.chi_squared.setReadOnly(True)
        chi_box.addWidget(QtWidgets.QLabel("Current chi-squared:"))
        chi_box.addWidget(self.chi_squared)

        # create dropdown to choose procedure
        procedure_selector = QtWidgets.QHBoxLayout()
        procedure_selector.addWidget(QtWidgets.QLabel("Procedure:"))
        self.procedure_dropdown = QtWidgets.QComboBox()
        self.procedure_dropdown.addItems([p.value for p in Procedures])
        self.procedure_dropdown.setCurrentIndex(init_procedure)
        self.procedure_dropdown.currentIndexChanged.connect(self.set_procedure)
        procedure_selector.addWidget(self.procedure_dropdown)

        # create button to hide/show fit settings
        self.fit_settings_button = QtWidgets.QPushButton()
        self.fit_settings_button.setCheckable(True)
        self.fit_settings_button.toggled.connect(self.toggle_fit_settings)
        self.fit_settings_button.toggle()  # to set true by default

        # compose buttons & widget
        procedure_box = QtWidgets.QVBoxLayout()
        procedure_box_buttons = QtWidgets.QVBoxLayout()
        procedure_box_buttons.addWidget(self.run_button)
        procedure_box_buttons.addLayout(procedure_selector)
        procedure_box_buttons.addWidget(self.fit_settings_button)
        procedure_box_buttons.setSpacing(20)
        procedure_box.addLayout(chi_box)
        procedure_box.addLayout(procedure_box_buttons)

        widget_layout = QtWidgets.QHBoxLayout()
        widget_layout.addLayout(procedure_box)
        widget_layout.addWidget(self.fit_settings)

        self.setLayout(widget_layout)

    def toggle_fit_settings(self, toggled: bool):
        """Toggle whether the fit settings table is visible.

        Parameters
        ----------
        toggled : bool
            Whether the button is toggled on or off.

        """
        if toggled:
            self.fit_settings.show()
            self.fit_settings_button.setText("Hide fit settings")
        else:
            self.fit_settings.hide()
            self.fit_settings_button.setText("Show fit settings")

    def toggle_run_button(self, toggled: bool):
        """Toggle whether the optimisation is currently running.

        Parameters
        ----------
        toggled : bool
            Whether the button is toggled on or off.

        """
        if toggled:
            self.fit_settings.setEnabled(False)
            self.procedure_dropdown.setEnabled(False)
            self.run_button.setText("Stop")
            self.run_button.setStyleSheet("background-color: red;")
            self.run_button.setIcon(self.stop_icon)
            # TODO some functional stuff... issue #9
            # self.presenter.run() etc.
            # presenter should send a signal when run is completed,
            # which then toggles the button back
        else:
            self.fit_settings.setEnabled(True)
            self.procedure_dropdown.setEnabled(True)
            self.run_button.setText("Run")
            self.run_button.setStyleSheet("background-color: green;")
            self.run_button.setIcon(self.play_icon)

    def set_procedure(self, index: int):
        """Change the Controls procedure and update the table.

        Parameters
        ----------
        index : int
            The index of the procedure to change to.

        """
        self.fit_settings_layout.setCurrentIndex(index)


class ValidatedInputWidget(QtWidgets.QWidget):
    """Number input for Pydantic field with validation."""

    def __init__(self, name: str, field_info: FieldInfo, parent=None):
        super().__init__(parent=parent)
        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel(name), 0, 0)
        self.name = name

        # editor_data and change_editor_data are set to the getter and setter
        # methods for the actual editor inside the widget
        self.editor_data: Callable
        self.change_editor_data: Callable
        self.edited_signal: QtCore.pyqtSignal

        if isinstance(field_info.annotation, int):
            self.value_box = QtWidgets.QSpinBox(self)
            set_constraints(self.value_box, field_info)
            self.editor_data = self.value_box.value
            self.change_editor_data = self.value_box.setValue
            self.edited_signal = self.value_box.valueChanged
        elif isinstance(field_info.annotation, float):
            self.value_box = QtWidgets.QDoubleSpinBox(self)
            set_constraints(self.value_box, field_info)
            self.editor_data = self.value_box.value
            self.change_editor_data = self.value_box.setValue
            self.edited_signal = self.value_box.valueChanged
        elif issubclass(field_info.annotation, Enum):
            self.value_box = QtWidgets.QComboBox(self)
            self.value_box.addItems(str(e.value) for e in field_info.annotation)
            self.editor_data = self.value_box.currentText
            self.change_editor_data = self.value_box.setCurrentText
            self.edited_signal = self.value_box.currentTextChanged
        elif isinstance(field_info.annotation, bool):
            self.value_box = QtWidgets.QCheckBox(self)
            self.editor_data = self.value_box.isChecked
            self.change_editor_data = self.value_box.setChecked
            self.edited_signal = self.value_box.checkStateChanged
        else:
            self.value_box = QtWidgets.QLineEdit(self)
            self.editor_data = self.value_box.text
            self.change_editor_data = self.value_box.setText
            self.edited_signal = self.value_box.textChanged

        layout.addWidget(self.value_box, 0, 1)

        self.validation_box = QtWidgets.QLabel()
        self.validation_box.setStyleSheet("QLabel { color : red; }")
        self.validation_box.font().setPointSize(10)
        self.validation_box.setFixedHeight(10)
        layout.addWidget(self.validation_box, 1, 1)

        self.setLayout(layout)

    def set_validation_text(self, msg: str):
        """Put a message in the validation box."""
        self.validation_box.setText(msg)


class FitSettingsWidget(QtWidgets.QWidget):
    def __init__(self, parent, procedure: Procedures, model: FitSettingsModel):
        super().__init__(parent)
        self.model = model
        self.rows = {}
        self.datasetter = {}
        self.visible_settings = self.model.get_procedure_settings(procedure)

        layout = QtWidgets.QVBoxLayout()
        for setting in self.visible_settings:
            field_info = self.model.model_fields[setting]
            self.rows[setting] = ValidatedInputWidget(setting, field_info)
            self.datasetter[setting] = self.create_model_data_setter(setting)
            self.rows[setting].edited_signal.connect(self.datasetter[setting])
            self.update_data(setting)
            layout.addWidget(self.rows[setting])

        self.setLayout(layout)

    def update_data(self, setting):
        self.rows[setting].change_editor_data(self.model.data(setting))

    def create_model_data_setter(self, setting: str) -> Callable:
        """Create a model data setter for the fit setting given by an integer.

        Parameters
        ----------
        s: str
            The setting to which the setter connects.

        """

        def set_model_data():
            value = self.rows[setting].editor_data()
            result = self.model.setData(setting, value)
            if result is False:
                self.rows[setting].set_validation_text(self.model.last_validation_error.errors()[0]["msg"])
            else:
                self.rows[setting].set_validation_text("")

        return set_model_data

def set_constraints(widget, field_info) -> None:
    pass
