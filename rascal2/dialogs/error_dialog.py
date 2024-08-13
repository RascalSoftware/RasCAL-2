"""Dialog for caught Python exceptions."""

from PyQt6 import QtWidgets


class ErrorDialog(QtWidgets.QDialog):
    """Dialog for Python errors."""

    def __init__(self, error: Exception, parent=None):
        super().__init__(parent)
        self.setWindowTitle(str(type(error)))

        self.layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel(str(error))
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.accept)

        self.layout.addWidget(label)
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)
