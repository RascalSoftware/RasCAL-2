from PyQt6 import QtCore, QtWidgets

from rascal2.core.settings import Settings, SettingsGroups
from rascal2.config import setup_settings
from rascal2.widgets.inputs import ValidatedInputWidget


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
        tab_widget.addTab(GeneralSettings(self), SettingsGroups.General)
        tab_widget.addTab(LoggingSettings(self), SettingsGroups.Logging)

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
        self.accept()

    def reset_default_settings(self):
        """Reset the settings to the global defaults"""
        self.parent().settings = Settings()
        self.accept()


class SettingsTab(QtWidgets.QWidget):
    def __init__(self, parent: SettingsDialog, group: str):
        super().__init__(parent)

        self.settings = parent.settings
        self.widgets = {}
        tab_layout = QtWidgets.QGridLayout()

        field_info = getattr(self.settings, "model_fields")
        group_settings = [key for (key, value) in field_info.items() if value.title == group]

        for i, setting in enumerate(group_settings):
            label_text = setting.replace("_", " ")
            tab_layout.addWidget(QtWidgets.QLabel(label_text), i, 0)
            self.widgets[setting] = ValidatedInputWidget(field_info[setting])
            try:
                self.widgets[setting].set_data(getattr(self.settings, setting))
            except TypeError:
                self.widgets[setting].set_data(str(getattr(self.settings, setting)))
            self.widgets[setting].edited_signal.connect(self.create_slot(setting))
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
    def __init__(self, parent: SettingsDialog):
        super().__init__(parent, SettingsGroups.General)


class LoggingSettings(SettingsTab):
    def __init__(self, parent: SettingsDialog):
        super().__init__(parent, SettingsGroups.Logging)
