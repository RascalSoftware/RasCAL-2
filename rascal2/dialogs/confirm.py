"""Confirmation dialog."""

from PyQt6 import QtWidgets


class ConfirmDialog(QtWidgets.QDialog):
    """Dialog to confirm an action."""

    def __init__(self, title, text, parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        message = QtWidgets.QLabel(text)
        layout.addWidget(message)
        layout.addWidget(button_box)
        self.setLayout(layout)
