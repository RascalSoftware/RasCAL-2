"""Widget for terminal display."""

import pkg_resources
from PyQt6 import QtGui, QtWidgets


class TerminalWidget(QtWidgets.QScrollArea):
    """Widget for displaying program output."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.text_area = QtWidgets.QPlainTextEdit()
        self.text_area.setReadOnly(True)
        font = QtGui.QFont()
        font.setFamily("Courier")
        font.setStyleHint(font.StyleHint.Monospace)
        self.text_area.setFont(font)
        self.text_area.setLineWrapMode(self.text_area.LineWrapMode.NoWrap)

        self.setWidget(self.text_area)
        self.setWidgetResizable(True)

        version = pkg_resources.get_distribution("rascal2").version
        self.append_text(
            """
 ███████████                       █████████    █████████   █████      
░░███░░░░░███                     ███░░░░░███  ███░░░░░███ ░░███       
 ░███    ░███   ██████    █████  ███     ░░░  ░███    ░███  ░███       
 ░██████████   ░░░░░███  ███░░  ░███          ░███████████  ░███       
 ░███░░░░░███   ███████ ░░█████ ░███          ░███░░░░░███  ░███       
 ░███    ░███  ███░░███  ░░░░███░░███     ███ ░███    ░███  ░███      █
 █████   █████░░████████ ██████  ░░█████████  █████   █████ ███████████
░░░░░   ░░░░░  ░░░░░░░░ ░░░░░░    ░░░░░░░░░  ░░░░░   ░░░░░ ░░░░░░░░░░░ 
"""
        )
        self.append_text(f"RasCAL-2: software for neutron reflectivity calculations v{version}")

    def append_text(self, text):
        """Append a line of text to the terminal."""
        self.text_area.appendPlainText(text)

    def clear(self):
        """Clear the text in the terminal."""
        self.text_area.setPlainText("")
        self.update()
