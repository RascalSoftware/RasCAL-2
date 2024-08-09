"""Widget for setting up the Controls class."""
from RATapi import Controls
from RATapi.controls import fields, common_fields
from RATapi.utils.enums import Procedures
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QLabel, QPushButton, QStackedWidget


def create_param_setter(param):
    return QLabel(param)


class MainWindowModel:
    #TODO: Remove once #11 merged
    def __init__(self):
        self.controls = Controls()


class ControlsWidget(QWidget):
    """Widget for editing the Controls object."""
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.controls = self.model.controls
        self.fit_settings = QStackedWidget()
        for procedure in Procedures:
            self.fit_settings.addWidget(FitSettingsWidget(procedure.value))

        procedure_selector = QHBoxLayout()
        procedure_selector.addWidget(QLabel("Procedure:"))
        procedure_dropdown = QComboBox()
        procedure_dropdown.addItems([p.value for p in Procedures])
        procedure_dropdown.setCurrentText(self.controls.procedure)
        procedure_dropdown.currentTextChanged.connect(self.set_fit_settings)
        procedure_selector.addWidget(procedure_dropdown)
        self.fit_settings_button = QPushButton()
        self.fit_settings_button.setCheckable(True)
        self.fit_settings_button.toggled.connect(self.toggle_fit_settings)
        self.fit_settings_button.toggle()  # to set true by default

        procedure_box = QVBoxLayout()
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

    def set_fit_settings(self, procedure):
        self.fit_settings.setCurrentIndex([p.value for p in Procedures].index(procedure))

class FitSettingsWidget(QWidget):
    def __init__(self, procedure):
        super().__init__()
        fit_settings_box = QVBoxLayout()
        fit_settings_box.addWidget(QLabel("Fit settings"))
        fit_settings = (f for f in fields[procedure] if f not in common_fields)
        for fit_setting in fit_settings:
            setting_label = QLabel(fit_setting)
            setting_value = create_param_setter(fit_setting)
            setting_row = QHBoxLayout()
            setting_row.addWidget(setting_label)
            setting_row.addWidget(setting_value)

            fit_settings_box.addLayout(setting_row)

        self.setLayout(fit_settings_box)

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
