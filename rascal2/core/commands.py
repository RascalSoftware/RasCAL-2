"""File for Qt commands."""

from pydantic_core import ValidationError
from PyQt6 import QtGui

from rascal2.dialogs import ErrorDialog


class editControls(QtGui.QUndoCommand):
    """Command for editing the Controls object."""

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
