from enum import StrEnum, unique

from PyQt6 import QtCore, QtWidgets

from rascal2.core.settings import Settings
from rascal2.widgets.inputs import ValidatedInputWidget


group_settings = {
    "General": ["style", "editor_fontsize", "terminal_fontsize"],
    "Logging": ["log_path", "log_level"],
    "Windows": ["mdi_defaults"]
}


class SettingsDialog(QtWidgets.QDialog):

    def __init__(self, parent):
        """
        Initialize dialog.

        Parameters
        ----------
        parent: MainWindowView
                An instance of the MainWindowView
        """
        super().__init__(parent)

        self.setModal(True)
        self.setMinimumWidth(700)

        current_settings = self.parent().settings

        tab_widget = QtWidgets.QTabWidget()
        tab_widget.addTab(GeneralSettings(self, current_settings), "General")
        tab_widget.addTab(LoggingSettings(self, current_settings), "Logging")
        tab_widget.addTab(WindowsSettings(self, current_settings), "Windows")

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(tab_widget)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)
        self.setWindowTitle("Settings")


class SettingsTab(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget, current_settings: Settings, group: str):
        super().__init__(parent)

        tab_layout = QtWidgets.QGridLayout()

        for i, setting in enumerate(group_settings[group]):
            label_text = setting.replace("_", " ")
            tab_layout.addWidget(QtWidgets.QLabel(label_text), i, 0)
            setting_widget = ValidatedInputWidget(getattr(current_settings, "model_fields")[setting])
            try:
                setting_widget.set_data(getattr(current_settings, setting))
            except TypeError:
                setting_widget.set_data(str(getattr(current_settings, setting)))
            tab_layout.addWidget(setting_widget, i, 1)

        tab_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.setLayout(tab_layout)


class GeneralSettings(SettingsTab):
    def __init__(self, parent: QtWidgets.QWidget, current_settings: Settings):
        super().__init__(parent, current_settings, "General")


class LoggingSettings(SettingsTab):
    def __init__(self, parent: QtWidgets.QWidget, current_settings: Settings):
        super().__init__(parent, current_settings, "Logging")


class WindowsSettings(SettingsTab):
    def __init__(self, parent: QtWidgets.QWidget, current_settings: Settings):
        super().__init__(parent, current_settings, "Windows")
