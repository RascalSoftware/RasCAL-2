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
        self.setMinimumWidth(400)

        self.current_settings = parent.settings.copy()

        tab_widget = QtWidgets.QTabWidget()
        tab_widget.addTab(GeneralSettings(self, self.current_settings), "General")
        tab_widget.addTab(LoggingSettings(self, self.current_settings), "Logging")
        tab_widget.addTab(WindowsSettings(self, self.current_settings), "Windows")

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        button_box.accepted.connect(self.update_settings)
        button_box.rejected.connect(self.reject_settings)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(tab_widget)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)
        self.setWindowTitle("Settings")

    def update_settings(self):
        """Accept the changed settings"""
        self.parent().settings = self.current_settings.copy()
        print(self.current_settings)
        print(self.parent().settings)
        self.accept()

    def reject_settings(self):
        """Accept the changed settings"""
        print(self.current_settings)
        print(self.parent().settings)
        self.reject()


class SettingsTab(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget, current_settings: Settings, group: str):
        super().__init__(parent)

        self.settings = current_settings
        tab_layout = QtWidgets.QGridLayout()

        self.widgets = {}
        self.slots = {}

        for i, setting in enumerate(group_settings[group]):
            label_text = setting.replace("_", " ")
            tab_layout.addWidget(QtWidgets.QLabel(label_text), i, 0)
            self.widgets[setting] = ValidatedInputWidget(getattr(current_settings, "model_fields")[setting])
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
        """Returns a slot that updates the settings to connect to the edited_signal of the given widget."""

        def modify_settings():
            setattr(self.settings, setting, self.widgets[setting].get_data())

        return modify_settings


class GeneralSettings(SettingsTab):
    def __init__(self, parent: QtWidgets.QWidget, current_settings: Settings):
        super().__init__(parent, current_settings, "General")


class LoggingSettings(SettingsTab):
    def __init__(self, parent: QtWidgets.QWidget, current_settings: Settings):
        super().__init__(parent, current_settings, "Logging")


class WindowsSettings(SettingsTab):
    def __init__(self, parent: QtWidgets.QWidget, current_settings: Settings):
        super().__init__(parent, current_settings, "Windows")
