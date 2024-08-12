"""File for Qt commands."""
from PyQt6.QtGui import QUndoCommand
from pydantic_core import ValidationError

from rascal2.dialogs import ErrorDialog

class editControls(QUndoCommand):
    """Class for """
    def __init__(self, controls, attr, value):
        super().__init__()
        self.controls = controls
        self.attr = attr
        self.value = value

    def undo(self):
        setattr(self.controls, self.attr, self.value)

    def redo(self):
        try:
            setattr(self.controls, self.attr, self.value)
        except ValidationError as err:
            dlg = ErrorDialog(err)
            dlg.exec()


