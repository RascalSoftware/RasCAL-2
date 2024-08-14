"""Widget for setting up the Controls class."""

from enum import Enum

from PyQt6 import QtGui, QtWidgets
from RATapi.utils.enums import Procedures

from rascal2.config import path_for
from rascal2.widgets.controls.model import FitSettingsModel
from rascal2.widgets.delegates import BoolDelegate, EnumDelegate

PLAY_BUTTON = QtGui.QIcon(path_for("play.png"))
STOP_BUTTON = QtGui.QIcon(path_for("stop.png"))


class ControlsWidget(QtWidgets.QWidget):
    """Widget for editing the Controls object."""

    def __init__(self, presenter):
        super().__init__()
        self.presenter = presenter
        init_procedure = self.presenter.model.controls.procedure  # to set to whatever initial procedure is saved

        self.fit_settings = QtWidgets.QTableView()
        self.fit_settings_model = FitSettingsModel(self.presenter)
        self.fit_settings.setModel(self.fit_settings_model)
        self.set_procedure(init_procedure)

        self.fit_settings.horizontalHeader().setVisible(False)
        self.fit_settings.horizontalHeader().setStretchLastSection(True)
        self.fit_settings.verticalHeader().setVisible(True)
        self.fit_settings.setShowGrid(False)
        self.fit_settings.setSelectionMode(self.fit_settings.SelectionMode.SingleSelection)

        self.run_button = QtWidgets.QPushButton(icon=PLAY_BUTTON, text="Run")
        self.run_button.setStyleSheet("background-color: green;")
        self.run_button.setCheckable(True)
        self.run_button.toggled.connect(self.toggle_run_button)

        chi_box = QtWidgets.QHBoxLayout()
        self.chi_squared = QtWidgets.QLineEdit("1.060")  # TODO hook this up when we can actually run... issue #9
        self.chi_squared.setReadOnly(True)
        chi_box.addWidget(QtWidgets.QLabel("Current chi-squared:"))
        chi_box.addWidget(self.chi_squared)

        procedure_selector = QtWidgets.QHBoxLayout()
        procedure_selector.addWidget(QtWidgets.QLabel("Procedure:"))
        self.procedure_dropdown = QtWidgets.QComboBox()
        self.procedure_dropdown.addItems([p.value for p in Procedures])
        self.procedure_dropdown.setCurrentText(init_procedure)
        self.procedure_dropdown.currentTextChanged.connect(self.set_procedure)
        procedure_selector.addWidget(self.procedure_dropdown)
        self.fit_settings_button = QtWidgets.QPushButton()
        self.fit_settings_button.setCheckable(True)
        self.fit_settings_button.toggled.connect(self.toggle_fit_settings)
        self.fit_settings_button.toggle()  # to set true by default

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

    def toggle_fit_settings(self, toggled):
        if toggled:
            self.fit_settings.show()
            self.fit_settings_button.setText("Hide fit settings")
        else:
            self.fit_settings.hide()
            self.fit_settings_button.setText("Show fit settings")

    def toggle_run_button(self, toggled):
        if toggled:
            self.fit_settings.setEnabled(False)
            self.procedure_dropdown.setEnabled(False)
            self.run_button.setText("Stop")
            self.run_button.setStyleSheet("background-color: red;")
            self.run_button.setIcon(STOP_BUTTON)
            # TODO some functional stuff... issue #9
            # self.presenter.run() etc.
            # presenter should send a signal when run is completed,
            # which then toggles the button back
        else:
            self.fit_settings.setEnabled(True)
            self.procedure_dropdown.setEnabled(True)
            self.run_button.setText("Run")
            self.run_button.setStyleSheet("background-color: green;")
            self.run_button.setIcon(PLAY_BUTTON)
            # TODO some functional stuff... issue #9
            # self.presenter.run() etc.

    def set_procedure(self, procedure):
        self.fit_settings_model.set_procedure(procedure)
        for i in range(0, len(self.fit_settings_model.fit_settings)):
            index = self.fit_settings_model.createIndex(i, 0)

            # set correct delegates for cells
            setting_datatype = self.fit_settings_model.datatypes[i]
            if issubclass(setting_datatype, Enum):
                self.fit_settings.setItemDelegateForRow(i, EnumDelegate(self, setting_datatype))
                self.fit_settings.openPersistentEditor(index)
            elif setting_datatype is bool:
                self.fit_settings.setItemDelegateForRow(i, BoolDelegate(self))
                self.fit_settings.openPersistentEditor(index)
            else:
                self.fit_settings.setItemDelegateForRow(i, QtWidgets.QStyledItemDelegate(self))
                self.fit_settings.closePersistentEditor(index)

        self.update()
