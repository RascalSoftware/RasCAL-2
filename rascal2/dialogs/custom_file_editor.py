"""Dialogs for editing custom files."""

import logging
from pathlib import Path

from PyQt6 import Qsci, QtWidgets
from RATapi.utils.enums import Languages
from RATapi.wrappers import start_matlab


def edit_file(filename: str, language: Languages, parent: QtWidgets.QWidget):
    """Edit a file in the file editor.

    Parameters
    ----------
    filename : str
        The name of the file to edit.
    language : Languages
        The language for dialog highlighting.
    parent : QtWidgets.QWidget
        The parent of this widget.

    """
    file = Path(filename)
    if not file.is_file():
        logger = logging.getLogger("rascal_log")
        logger.error("Attempted to edit a custom file which does not exist!")
        return

    dialog = CustomFileEditorDialog(file, language, parent)
    dialog.exec()


def edit_file_matlab(filename: str):
    """Open a file in MATLAB."""
    loader = start_matlab()

    if loader is None:
        logger = logging.getLogger("rascal_log")
        logger.error("Attempted to edit a file in MATLAB engine, but `matlabengine` is not available.")
        return

    engine = loader.result()
    engine.edit(str(filename))


class CustomFileEditorDialog(QtWidgets.QDialog):
    """Dialog for editing custom files.

    Parameters
    ----------
    file : pathlib.Path
        The file to edit.
    language : Languages
        The language for dialog highlighting.
    parent : QtWidgets.QWidget
        The parent of this widget.

    """

    def __init__(self, file, language, parent):
        super().__init__(parent)

        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self.file = file

        self.editor = Qsci.QsciScintilla()
        match language:
            case Languages.Python:
                self.editor.setLexer(Qsci.QsciLexerPython(self.editor))
            case Languages.Matlab:
                self.editor.setLexer(Qsci.QsciLexerMatlab(self.editor))
            case _:
                self.editor.setLexer(None)

        self.editor.setText(self.file.read_text())

        save_button = QtWidgets.QPushButton("Save", self)
        save_button.clicked.connect(self.save_file)
        cancel_button = QtWidgets.QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.reject)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.editor)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setWindowTitle(f"Edit {str(file)}")

    def save_file(self):
        """Save and close the file."""
        self.file.write_text(self.editor.text())
        self.accept()
