"""Delegates for items in Qt tables."""

from typing import Literal

from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.widgets.inputs import AdaptiveDoubleSpinBox, get_validated_input


class ValidatedInputDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for validated inputs."""

    def __init__(self, field_info, parent):
        super().__init__(parent)
        self.table = parent
        self.field_info = field_info

    def createEditor(self, parent, option, index):
        widget = get_validated_input(self.field_info, parent)
        widget.set_data(index.data(QtCore.Qt.ItemDataRole.DisplayRole))

        # without this signal, data isn't committed unless the user presses 'enter' on the cell
        widget.edited_signal.connect(lambda: self.table.commitData(widget))

        # fill in background as otherwise you can see the original View text underneath
        widget.setAutoFillBackground(True)
        widget.setBackgroundRole(QtGui.QPalette.ColorRole.Base)

        return widget

    def setEditorData(self, editor: QtWidgets.QWidget, index):
        data = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        editor.set_data(data)

    def setModelData(self, editor, model, index):
        data = editor.get_data()
        model.setData(index, data, QtCore.Qt.ItemDataRole.EditRole)


class ValueSpinBoxDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for parameter values between a dynamic min and max.

    Parameters
    ----------
    field : Literal["min", "value", "max"]
        The field of the parameter

    """

    _error_style = "color: #E34234"

    def __init__(self, field: Literal["min", "value", "max"], parent):
        super().__init__(parent)
        self.table = parent
        self.field = field

    def createEditor(self, parent, option, index):
        widget = AdaptiveDoubleSpinBox(parent)

        # without this signal, data isn't committed unless the user presses 'enter' on the cell
        widget.valueChanged.connect(lambda: self.table.commitData(widget))

        # fill in background as otherwise you can see the original View text underneath
        widget.setAutoFillBackground(True)
        widget.setBackgroundRole(QtGui.QPalette.ColorRole.Base)

        return widget

    def setEditorData(self, editor: AdaptiveDoubleSpinBox, index):
        data = index.data(QtCore.Qt.ItemDataRole.DisplayRole)

        editor.setValue(data)

    def setModelData(self, editor: AdaptiveDoubleSpinBox, model, index):
        data = editor.value()
        max_val = float("inf")
        min_val = -float("inf")

        if self.field in ["min", "value"]:
            max_val = index.siblingAtColumn(index.column() + 1).data(QtCore.Qt.ItemDataRole.DisplayRole)
        if self.field in ["value", "max"]:
            min_val = index.siblingAtColumn(index.column() - 1).data(QtCore.Qt.ItemDataRole.DisplayRole)
        if data > max_val:
            editor.setValue(max_val)
        elif data < min_val:
            editor.setValue(min_val)
        else:
            model.setData(index, data, QtCore.Qt.ItemDataRole.EditRole)
