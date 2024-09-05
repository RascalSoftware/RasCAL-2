"""Widget for terminal display."""

import logging
from importlib import metadata

from PyQt6 import QtGui, QtWidgets


class TerminalWidget(QtWidgets.QWidget):
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

        widget_layout = QtWidgets.QVBoxLayout()

        self.scroll_text = QtWidgets.QScrollArea()
        self.scroll_text.setWidget(self.text_area)
        self.scroll_text.setWidgetResizable(True)
        widget_layout.addWidget(self.scroll_text)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximumHeight(15)
        self.progress_bar.setMinimumHeight(10)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setVisible(False)
        widget_layout.addWidget(self.progress_bar)

        widget_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(widget_layout)

        version = metadata.version("rascal2")
        self.write(
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
        self.write_html(f"<b>RasCAL-2:</b> software for neutron reflectivity calculations <b>v{version}</b>")

    def write(self, text):
        self.text_area.appendPlainText(text)

    def write_html(self, text):
        """Append HTML text to the terminal."""
        self.text_area.appendHtml(text)

    def clear(self):
        """Clear the text in the terminal."""
        self.text_area.setPlainText("")
        self.update()

    def update_progress(self, event):
        """Update the progress bar from event data.

        Parameters
        ----------
        event : ProgressEventData
            The data for the current event.

        """
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(int(event.percent * 100))

    # added to make TerminalWidget an IO stream
    def flush(self):
        pass
