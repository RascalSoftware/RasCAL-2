"""Widget for setting up the Controls class."""
from enum import Enum

from RATapi import Controls
from RATapi.controls import fields, common_fields
from RATapi.utils.enums import Procedures
from PyQt6.QtCore import QModelIndex, Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QLabel, QPushButton, QTableView, QStyledItemDelegate, QCheckBox
from PyQt6.QtGui import QUndoStack, QIcon, QShortcut, QKeySequence

from rascal2.ui.model import FitSettingsModel
from rascal2.config import path_for
from rascal2.core.commands import editControls


PLAY_BUTTON = QIcon(path_for("play.png"))
STOP_BUTTON = QIcon(path_for("stop.png"))


class MainWindowModel:
    #TODO: Remove once #11 merged
    def __init__(self):
        self.controls = Controls()


class ControlsWidget(QWidget):
    """Widget for editing the Controls object."""
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.undo_stack = QUndoStack(self)
        self.controls = self.model.controls

        self.fit_settings = QTableView()
        self.fit_settings_model = FitSettingsModel(self.controls, self.undo_stack)
        self.fit_settings.setModel(self.fit_settings_model)
        self.fit_settings.horizontalHeader().setVisible(False)
        self.fit_settings.verticalHeader().setVisible(True)

        self.run_button = QPushButton(icon=PLAY_BUTTON, text="Run")
        self.run_button.setStyleSheet('background-color: green;')
        self.run_button.setIcon(PLAY_BUTTON)
        self.run_button.setCheckable(True)
        self.run_button.toggled.connect(self.toggle_run_button)

        procedure_selector = QHBoxLayout()
        procedure_selector.addWidget(QLabel("Procedure:"))
        self.procedure_dropdown = QComboBox()
        self.procedure_dropdown.addItems([p.value for p in Procedures])
        self.procedure_dropdown.setCurrentText(self.controls.procedure)
        self.procedure_dropdown.currentTextChanged.connect(self.set_procedure)
        procedure_selector.addWidget(self.procedure_dropdown)
        self.fit_settings_button = QPushButton()
        self.fit_settings_button.setCheckable(True)
        self.fit_settings_button.toggled.connect(self.toggle_fit_settings)
        self.fit_settings_button.toggle()  # to set true by default

        procedure_box = QVBoxLayout()
        procedure_box.addWidget(self.run_button)
        procedure_box.addLayout(procedure_selector)
        procedure_box.addWidget(self.fit_settings_button)

        widget_layout = QHBoxLayout()
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
            self.run_button.setIcon(STOP_BUTTON)
            self.run_button.setStyleSheet('background-color: red;')
            # TODO some functional stuff... issue #9
        else:
            self.fit_settings_model.editable = True
            self.procedure_dropdown.setEnabled(True)
            self.run_button.setText("Run")
            self.run_button.setIcon(PLAY_BUTTON)
            self.run_button.setStyleSheet('background-color: green;')
            # TODO some functional stuff... issue #9

    def set_procedure(self, procedure):
        self.fit_settings_model.set_procedure(procedure)
        self.update()


from PyQt6.QtWidgets import QApplication, QMainWindow
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        model = MainWindowModel()
        widget = ControlsWidget(model)
        self.setCentralWidget(widget)

app = QApplication([])

window = MainWindow()
window.show()

app.exec()
