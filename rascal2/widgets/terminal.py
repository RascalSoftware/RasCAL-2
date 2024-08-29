"""Widget for terminal display."""

import logging
from importlib import metadata

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

        self.logger = logging.getLogger("log")

        self.setWidget(self.text_area)
        self.setWidgetResizable(True)

        version = metadata.version("rascal2")
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
        self.append_html(f"<b>RasCAL-2:</b> software for neutron reflectivity calculations <b>v{version}</b>")

    def append_text(self, text):
        """Append a line of text to the terminal."""
        self.text_area.appendPlainText(text)

    def append_html(self, text):
        """Append HTML text to the terminal."""
        self.text_area.appendHtml(text)

    def clear(self):
        """Clear the text in the terminal."""
        self.text_area.setPlainText("")
        self.update()
