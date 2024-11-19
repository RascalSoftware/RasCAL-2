"""Delegates for items in Qt tables."""

from typing import Literal

from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.widgets.inputs import AdaptiveDoubleSpinBox, MultiSelectComboBox, get_validated_input


class ValidatedInputDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for validated inputs."""

    def __init__(self, field_info, parent):
        super().__init__(parent)
        self.table = parent
        self.field_info = field_info

    def createEditor(self, parent, option, index):
        widget = get_validated_input(self.field_info, parent)
        widget.set_data(index.data(QtCore.Qt.ItemDataRole.DisplayRole))

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

    def __init__(self, field: Literal["min", "value", "max"], parent):
        super().__init__(parent)
        self.table = parent
        self.field = field

    def createEditor(self, parent, option, index):
        widget = AdaptiveDoubleSpinBox(parent)

        max_val = float("inf")
        min_val = -float("inf")

        if self.field in ["min", "value"]:
            max_val = index.siblingAtColumn(index.column() + 1).data(QtCore.Qt.ItemDataRole.DisplayRole)
        if self.field in ["value", "max"]:
            min_val = index.siblingAtColumn(index.column() - 1).data(QtCore.Qt.ItemDataRole.DisplayRole)

        widget.setMinimum(min_val)
        widget.setMaximum(max_val)

        # fill in background as otherwise you can see the original View text underneath
        widget.setAutoFillBackground(True)
        widget.setBackgroundRole(QtGui.QPalette.ColorRole.Base)

        return widget

    def setEditorData(self, editor: AdaptiveDoubleSpinBox, index):
        data = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        editor.setValue(data)

    def setModelData(self, editor, model, index):
        data = editor.value()
        model.setData(index, data, QtCore.Qt.ItemDataRole.EditRole)


class ParametersDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate to choose from existing draft project parameters."""

    def __init__(self, project_widget, parent):
        super().__init__(parent)
        self.project_widget = project_widget

    def createEditor(self, parent, option, index):
        widget = QtWidgets.QComboBox(parent)
        parameters = self.project_widget.draft_project["parameters"]
        names = [p.name for p in parameters]
        widget.addItems(names)
        widget.setCurrentText(index.data(QtCore.Qt.ItemDataRole.DisplayRole))

        return widget

    def setEditorData(self, editor: QtWidgets.QWidget, index):
        data = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        editor.setCurrentText(data)

    def setModelData(self, editor, model, index):
        data = editor.currentText()
        model.setData(index, data, QtCore.Qt.ItemDataRole.EditRole)

class MultiSelectLayerDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for multiselecting layers."""

    def __init__(self, project_widget, parent):
        super().__init__(parent)
        self.project_widget = project_widget

    def createEditor(self, parent, option, index):
        widget = MultiSelectComboBox(parent)

        layers = self.project_widget.draft_project["layers"]
        widget.addItems([layer.name for layer in layers])

        current_layers = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        widget.select_indices([i for i, layer in enumerate(layers) if layer in current_layers])

        return widget

    def setEditorData(self, editor: MultiSelectComboBox, index):
        data = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        editor.select_indices([i for i, layer in enumerate(data) if layer in data])

    def setModelData(self, editor, model, index):
        data = editor.selected_items()
        model.setData(index, data, QtCore.Qt.ItemDataRole.EditRole)
