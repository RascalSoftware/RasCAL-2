"""Dialogs for editing custom files."""

import os
import re
from pathlib import Path

from PyQt6 import Qsci, QtGui, QtWidgets
from ratapi.utils.enums import Languages

from rascal2.config import LOGGER, SETTINGS, MatlabHelper
from rascal2.core.enums import CustomFileType
from rascal2.paths import EXAMPLES_PATH

MATLAB_MODEL_TEMPLATE = """function [output, sub_rough] = {0}{1}
% RasCAL-2 Layer Model Custom File.
%
% The first 3 arguments are vectors containing the values for parameters, bulk in and bulk out
% The fourth argument is a number indicating which contrast is being calculated (this number starts from 1)
% {2}
% This function should return an array of layer values in the form:
% output = [Thickness 1, SLD 1, Roughness 1, Percent Hydration 1, Hydrate how 1;
%           ....
%           Thickness n, SLD n, Roughness n, Percent Hydration n, Hydrate how n]
% The "Hydrate how" parameter decides if the layer is hydrated with
% Bulk in or Bulk out phases. Set to 0 for Bulk in or 1 for Bulk out.
% Alternatively, leave out hydration and just return:
% output = [Thickness 1, SLD 1, Roughness 1;
%           ....
%           Thickness n, SLD n, Roughness n];
% The second output parameter should be the substrate roughness."""


PYTHON_MODEL_TEMPLATE = """def {0}{1}:
    \"\"\"RasCAL-2 Layer Model Custom File.
    
    The first 3 arguments are vectors containing the values for parameters, bulk in and bulk out
    The fourth argument is a number indicating which contrast is being calculated (this number starts from 1)
    {2}
    This function should return a tuple with 2 entries. The first entry is an array of layer values in the form:
    output = [[Thickness 1, SLD 1, Roughness 1, Percent Hydration 1, Hydrate how 1],
               ....
              [Thickness n, SLD n, Roughness n, Percent Hydration n, Hydrate how n]]
    The "Hydrate how" parameter decides if the layer is hydrated with
    Bulk in or Bulk out phases. Set to 0 for Bulk in or 1 for Bulk out.
    Alternatively, leave out hydration and just return:
    output = [[Thickness 1, SLD 1, Roughness 1]
               ....
              [Thickness n, SLD n, Roughness n]]
    The second output parameter should be the substrate roughness.\"\"\"
"""


PYTHON_BACKGROUND_TEMPLATE = """def {0}(xdata, params):
    \"\"\"RasCAL-2 Background Custom File.
    
    The first argument is a vector containing the q points over the simulation range, which should incorporate 
    the q values of the supplied data.
    The second argument is a vector containing the background parameters associated with the background.
    
    This function should return an array with the background value for each of the input simulation points.\"\"\"
"""


MATLAB_BACKGROUND_TEMPLATE = """function background = {0}(xdata, params)
% RasCAL-2 Background Custom File.
%
% The first argument is a vector containing the q points over the simulation range, which should incorporate 
% the q values of the supplied data.
% The second argument is a vector containing the background parameters associated with the background.
%
% This function should return an array with the background value for each of the input simulation points."""


def create_new_file(
    name: str, language: Languages, is_domains: bool, file_type: CustomFileType, parent: QtWidgets.QWidget
):
    """Create a new file using a template and opens the file in the editor.

    Parameters
    ----------
    name : str
        The unique name used to generate filename.
    language : str
        The language of file
    is_domains : str
        Indicates if the file is for domains project.
    file_type : CustomFileType
        The type of custom file i.e. model or background.
    parent : str
        The parent of editor widget.

    Returns
    -------
    filename: str
        The path of the new custom file.
    """
    # remove symbols from name since this will be used for file and function name
    name = re.sub(r"[^\w]", "", name.replace(" ", "_"))
    function_name = name.lower()
    if language == Languages.Python:
        ext = ".py"
        comment = PYTHON_MODEL_TEMPLATE if file_type == CustomFileType.Model else PYTHON_BACKGROUND_TEMPLATE
        signature = "(params, bulk_in, bulk_out, contrast{0})"
    elif language == Languages.Matlab:
        ext = ".m"
        comment = MATLAB_MODEL_TEMPLATE if file_type == CustomFileType.Model else MATLAB_BACKGROUND_TEMPLATE
        signature = "(params, bulkIn, bulkOut, contrast{0})"
    else:
        LOGGER.error(f"Creating a new file for {language} is not supported.")
        return

    filename = f"{function_name}{ext}"
    if file_type == CustomFileType.Model:
        signature = signature.format(", domain" if is_domains else "")
        extra = (
            "The fifth argument is a number indicating which domain is being calculated (this number starts from 1).\n"
            if is_domains
            else ""
        )
        comment = comment.format(function_name, signature, extra)
    else:
        comment = comment.format(function_name)

    if Path(filename).is_file():
        LOGGER.error(f"The file ({filename}) already exists, change custom file name to create a different file.")
        return

    with open(filename, "w") as f:
        f.write(comment)

    edit_file(filename, language, parent)
    return filename


def edit_file(filename: str, language: Languages, parent: QtWidgets.QWidget):
    """Edit a file in the user's default file editor.

    Parameters
    ----------
    filename : str
        The name of the file to edit.
    language : Languages
        The language for dialog highlighting.
    parent : QtWidgets.QWidget
        The parent of this widget.

    """
    use_matlab = SETTINGS.matlab_as_default_editor or language == Languages.Matlab
    if use_matlab and edit_file_matlab(filename):
        return

    # Always fallback to RasCAL editor if MATLAB is not available
    edit_file_local(filename, language, parent)


def edit_file_local(filename: str, language: Languages, parent: QtWidgets.QWidget):
    """Edit a file in the RasCAL file editor.

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
        LOGGER.error("Attempted to edit a custom file which does not exist!")
        return

    dialog = CustomFileEditorDialog(parent)
    dialog.open_file(file, language)
    dialog.setModal(False)
    dialog.show()


def edit_file_matlab(filename: str):
    """Open a file in MATLAB."""
    try:
        engine = MatlabHelper().get_local_engine()
    except Exception as ex:
        LOGGER.error("Attempted to edit a file in MATLAB engine", exc_info=ex)
        return False

    engine.cd(os.getcwd())
    engine.edit(str(filename))
    return True


class Singleton(type(QtWidgets.QDialog), type):
    """Metaclass used to create a PyQt singleton."""

    def __init__(cls, name, bases, cls_dict):
        super().__init__(name, bases, cls_dict)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class CustomFileEditorDialog(QtWidgets.QDialog, metaclass=Singleton):
    """Dialog for editing custom files.

    Parameters
    ----------
    parent : QtWidgets.QWidget
        The parent of this widget.

    """

    def __init__(self, parent):
        super().__init__(parent)

        self.file = None
        self.unchanged_text = ""
        self.editor = Qsci.QsciScintilla()
        self.editor.setBraceMatching(Qsci.QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QtGui.QColor("#cccccc"))
        self.editor.setScrollWidth(1)
        self.editor.setEolMode(Qsci.QsciScintilla.EolMode.EolUnix)
        self.editor.setScrollWidthTracking(True)
        self.editor.setFolding(Qsci.QsciScintilla.FoldStyle.PlainFoldStyle)
        self.editor.setIndentationsUseTabs(False)
        self.editor.setIndentationGuides(True)
        self.editor.setAutoIndent(True)
        self.editor.setTabWidth(4)

        font = self.default_font
        self.editor.setFont(font)
        # Margin 0 is used for line numbers
        font_metrics = QtGui.QFontMetrics(font)
        self.editor.setMarginsFont(font)
        self.editor.setMarginWidth(0, font_metrics.horizontalAdvance("00000") + 6)
        self.editor.setMarginLineNumbers(0, True)
        self.editor.setMarginsBackgroundColor(QtGui.QColor("#cccccc"))
        self.editor.textChanged.connect(self.show_modified)

        save_button = QtWidgets.QPushButton("Save", self)
        save_button.clicked.connect(self.save_file)
        close_button = QtWidgets.QPushButton("Close", self)
        close_button.clicked.connect(self.reject)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(save_button)
        button_layout.addWidget(close_button)
        button_layout.addSpacing(10)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.editor)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        layout.setContentsMargins(0, 0, 0, 0)

    @property
    def default_font(self):
        """Return default editor font.

        Returns
        -------
        font : QtGui.QFont
            The default font.

        """
        # Set the default font
        font = QtGui.QFont("Courier", 10)
        font.setFixedPitch(True)
        return font

    @property
    def is_modified(self):
        """Return if document is modified.

        Returns
        -------
        modified : bool
            Indicates if document is modified.

        """
        return self.unchanged_text != self.editor.text()

    def show_modified(self):
        """Show modified state in window title."""
        pre = "* " if self.is_modified else ""
        self.setWindowTitle(f"{pre}Edit {str(self.file)}")

    def open_file(self, file, language):
        """Open a custom file.

        Parameters
        ----------
        file : pathlib.Path
            The file to edit.
        language : Languages
            The language for dialog highlighting.
        """
        if file == self.file:
            return  # file is already opened

        if self.is_modified:
            result = QtWidgets.QMessageBox.question(
                self,
                "Save File",
                "Do you want to save changes to this file?",
                QtWidgets.QMessageBox.StandardButton.Discard | QtWidgets.QMessageBox.StandardButton.Save,
                QtWidgets.QMessageBox.StandardButton.Save,
            )
            if result == QtWidgets.QMessageBox.StandardButton.Save:
                self.save_file()

        self.file = file
        self.setWindowTitle(f"Edit {str(file)}")
        match language:
            case Languages.Python:
                self.editor.setLexer(Qsci.QsciLexerPython(self.editor))
            case Languages.Matlab:
                self.editor.setLexer(Qsci.QsciLexerMatlab(self.editor))
            case _:
                self.editor.setLexer(None)

        if self.editor.lexer() is not None:
            self.editor.lexer().setFont(self.default_font)
        self.unchanged_text = self.file.read_text(encoding="utf-8", errors="backslashreplace")
        self.editor.setText(self.unchanged_text)
        self.editor.setModified(False)
        self.setWindowModified(False)

    def save_file(self):
        """Save the custom file."""
        if not self.is_modified:
            return

        if self.file.is_relative_to(EXAMPLES_PATH):
            message = "Files cannot be saved into the examples directory, please copy the file to another directory."
            QtWidgets.QMessageBox.warning(self, "Save File", message, QtWidgets.QMessageBox.StandardButton.Ok)
            return

        try:
            self.file.write_text(self.editor.text(), encoding="utf-8")
            self.unchanged_text = self.editor.text()
            self.show_modified()
        except OSError as ex:
            message = f"Failed to save custom file to {self.file}.\n"
            LOGGER.error(message, exc_info=ex)
            QtWidgets.QMessageBox.critical(self, "Save File", message, QtWidgets.QMessageBox.StandardButton.Ok)

    def reject(self):
        CustomFileEditorDialog._instance = None
        super().reject()
