import warnings

from pydantic_core import ValidationError
import RATapi as RAT
from PyQt6 import QtCore
from RATapi.controls import common_fields, fields
from RATapi.utils.enums import Procedures

from rascal2.core.commands import editControls
from rascal2.dialogs import ErrorDialog


class MainWindowModel(QtCore.QObject):
    """Manages project data and communicates to view via signals"""

    def __init__(self):
        super().__init__()

        self.project = None
        self.results = None
        self.controls = None

        self.save_path = ""

    def create_project(self, name: str, save_path: str):
        """Creates a new RAT project and controls object.

        Parameters
        ----------
        name : str
            The name of the project.
        save_path : str
            The save path of the project.
        """
        self.project = RAT.Project(name=name)
        self.controls = RAT.Controls()
        self.save_path = save_path


class FitSettingsModel(QtCore.QAbstractTableModel):
    """Model for Controls fit settings."""

    def __init__(self, controls, undo_stack):
        super().__init__()
        self.controls = controls
        self.undo_stack = undo_stack
        self.set_procedure(self.controls.procedure)
        self.editable = True

    def columnCount(self, parent=None):
        return 1

    def rowCount(self, parent=None):
        return len(self.fit_settings)

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole and orientation == QtCore.Qt.Orientation.Vertical:
            return self.fit_settings[section]
        return None

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        i = index.row()
        fit_setting = self.fit_settings[i]
        value = getattr(self.controls, fit_setting)
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return str(value)

    def setData(self, index, value, role):
        i = index.row()
        fit_setting = self.fit_settings[i]
        # we have to check validation in advance because PyQt doesn't return
        # the exception, it just falls over in C++
        # also doing it this way stops bad changes being pushed onto the stack
        if role == QtCore.Qt.ItemDataRole.EditRole:
            try:
                with warnings.catch_warnings():  # warning is erroneous...
                    warnings.simplefilter("ignore")
                    self.controls.model_validate({fit_setting: value})
            except ValidationError as err:
                dlg = ErrorDialog(err)
                dlg.exec()
                return False
            self.undo_stack.push(editControls(self.controls, fit_setting, value))
            self.dataChanged.emit(index, index, [])
            return True

    def flags(self, index):
        if self.editable:
            return QtCore.Qt.ItemFlag.ItemIsEditable | QtCore.Qt.ItemFlag.ItemIsUserCheckable | super().flags(index)
        return super().flags(index)

    def set_procedure(self, procedure: Procedures):
        self.beginResetModel()
        # don't bother with the undo stack because the underlying data values are still saved
        self.controls.procedure = procedure
        self.fit_settings = [f for f in fields[procedure] if f not in common_fields]
        self.endResetModel()
