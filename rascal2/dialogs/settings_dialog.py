from enum import StrEnum, unique

from PyQt6 import QtWidgets


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

        tab_widget = QtWidgets.QTabWidget()
        tab_widget.addTab(GeneralSettings(self), "General")
        tab_widget.addTab(LoggingSettings(self), "Logging")
        tab_widget.addTab(WindowsSettings(self), "Windows")

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


class GeneralSettings(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)


class LoggingSettings(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)


class WindowsSettings(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
