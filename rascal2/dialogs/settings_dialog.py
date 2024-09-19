from PyQt6 import QtCore, QtWidgets

from rascal2.core.settings import Settings
from rascal2.config import setup_settings
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
        self.setMinimumWidth(400)

        self.settings = parent.settings.copy()

        tab_widget = QtWidgets.QTabWidget()
        tab_widget.addTab(GeneralSettings(self), "General")
        tab_widget.addTab(LoggingSettings(self), "Logging")
        tab_widget.addTab(WindowsSettings(self), "Windows")

        self.reset_button = QtWidgets.QPushButton("Reset Defaults", self)
        self.reset_button.clicked.connect(self.reset_default_settings)
        self.accept_button = QtWidgets.QPushButton("OK", self)
        self.accept_button.clicked.connect(self.update_settings)
        self.cancel_button = QtWidgets.QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.accept_button)
        button_layout.addWidget(self.cancel_button)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(tab_widget)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        self.setWindowTitle("Settings")

    def update_settings(self):
        """Accept the changed settings"""
        self.parent().settings = self.settings.copy()
        print(self.settings)
        print(self.parent().settings)
        self.accept()

    def reset_default_settings(self):
        """Reset the settings to the global defaults"""
        self.parent().settings = Settings()
        print(self.settings)
        print(self.parent().settings)
        self.accept()


class SettingsTab(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget, group: str):
        super().__init__(parent)

        self.settings = parent.settings
        tab_layout = QtWidgets.QGridLayout()

        self.widgets = {}
        self.slots = {}

        for i, setting in enumerate(group_settings[group]):
            label_text = setting.replace("_", " ")
            tab_layout.addWidget(QtWidgets.QLabel(label_text), i, 0)
            self.widgets[setting] = ValidatedInputWidget(getattr(self.settings, "model_fields")[setting])
            try:
                self.widgets[setting].set_data(getattr(self.settings, setting))
            except TypeError:
                self.widgets[setting].set_data(str(getattr(self.settings, setting)))
            self.slots[setting] = self.create_slot(setting)
            self.widgets[setting].edited_signal.connect(self.slots[setting])
            tab_layout.addWidget(self.widgets[setting], i, 1)

        tab_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.setLayout(tab_layout)

    def create_slot(self, setting):
        """Returns a slot that updates the settings.

        Connect this to the "edited_signal" of the given widget.
        """

        def modify_settings():
            setattr(self.settings, setting, self.widgets[setting].get_data())

        return modify_settings


class GeneralSettings(SettingsTab):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent, "General")


class LoggingSettings(SettingsTab):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent, "Logging")


class WindowsSettings(SettingsTab):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent, "Windows")
