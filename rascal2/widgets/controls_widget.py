"""Widget for setting up the Controls class."""
from enum import Enum

from PyQt6 import QtGui, QtWidgets, QtCore
from RATapi.utils.enums import Procedures

from rascal2.config import path_for
from rascal2.ui.model import FitSettingsModel

PLAY_BUTTON = QtGui.QIcon(path_for("play.png"))
STOP_BUTTON = QtGui.QIcon(path_for("stop.png"))


class ControlsWidget(QtWidgets.QWidget):
    """Widget for editing the Controls object."""

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.undo_stack = QtGui.QUndoStack(self)
        self.controls = self.model.controls

        self.fit_settings = QtWidgets.QTableView()
        self.fit_settings_model = FitSettingsModel(self.controls, self.undo_stack)
        self.fit_settings.setModel(self.fit_settings_model)
        self.set_procedure(self.controls.procedure)
        self.fit_settings.horizontalHeader().setVisible(False)
        self.fit_settings.horizontalHeader().setStretchLastSection(True)
        self.fit_settings.verticalHeader().setVisible(True)

        self.run_button = QtWidgets.QPushButton(icon=PLAY_BUTTON, text="Run")
        self.run_button.setStyleSheet("background-color: green;")
        self.run_button.setCheckable(True)
        self.run_button.toggled.connect(self.toggle_run_button)

        procedure_selector = QtWidgets.QHBoxLayout()
        procedure_selector.addWidget(QtWidgets.QLabel("Procedure:"))
        self.procedure_dropdown = QtWidgets.QComboBox()
        self.procedure_dropdown.addItems([p.value for p in Procedures])
        self.procedure_dropdown.setCurrentText(self.controls.procedure)
        self.procedure_dropdown.currentTextChanged.connect(self.set_procedure)
        procedure_selector.addWidget(self.procedure_dropdown)
        self.fit_settings_button = QtWidgets.QPushButton()
        self.fit_settings_button.setCheckable(True)
        self.fit_settings_button.toggled.connect(self.toggle_fit_settings)
        self.fit_settings_button.toggle()  # to set true by default

        procedure_box = QtWidgets.QVBoxLayout()
        procedure_box.addWidget(self.run_button)
        procedure_box.addLayout(procedure_selector)
        procedure_box.addWidget(self.fit_settings_button)

        widget_layout = QtWidgets.QHBoxLayout()
        widget_layout.addLayout(procedure_box)
        widget_layout.addWidget(self.fit_settings)

        self.setLayout(widget_layout)

    def toggle_fit_settings(self, toggled):
        if toggled:
            self.fit_settings.show()
            self.fit_settings_button.setText("Hide fit settings")
        else:
            self.fit_settings.hide()
            self.fit_settings_button.setText("Show fit settings")

    def toggle_run_button(self, toggled):
        if toggled:
            self.fit_settings_model.editable = False
            self.procedure_dropdown.setEnabled(False)
            self.run_button.setText("Stop")
            self.run_button.setStyleSheet("background-color: red;")
            self.run_button.setIcon(STOP_BUTTON)
            # TODO some functional stuff... issue #9
        else:
            self.fit_settings_model.editable = True
            self.procedure_dropdown.setEnabled(True)
            self.run_button.setText("Run")
            self.run_button.setStyleSheet("background-color: green;")
            self.run_button.setIcon(PLAY_BUTTON)
            # TODO some functional stuff... issue #9

    def set_procedure(self, procedure):
        self.fit_settings_model.set_procedure(procedure)
        for i, setting in enumerate(self.fit_settings_model.fit_settings):
            value = getattr(self.controls, setting)
            if isinstance(value, Enum):
                self.fit_settings.setItemDelegateForRow(i, EnumDelegate(self, value))
            elif isinstance(value, bool):
                self.fit_settings.setItemDelegateForRow(i, BoolDelegate(self))
            else:
                self.fit_settings.setItemDelegateForRow(i, QtWidgets.QStyledItemDelegate(self))
        self.update()


class EnumDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for Enums."""
    def __init__(self, parent, enum):
        super().__init__(parent)
        self.enum = type(enum)

    def createEditor(self, parent, option, index):
        combobox = QtWidgets.QComboBox(parent)
        combobox.addItems(e.value for e in self.enum)
        return combobox


class BoolDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for bools."""
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        return QtWidgets.QCheckBox(parent)
