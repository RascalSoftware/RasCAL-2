"""Delegates for items in Qt tables."""

from enum import Enum
from pathlib import Path
from typing import Literal

from PyQt6 import QtCore, QtGui, QtWidgets
from ratapi.utils.enums import TypeOptions

from rascal2.widgets.inputs import AdaptiveDoubleSpinBox, MultiSelectList, get_validated_input


class ValidatedInputDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for validated inputs."""

    def __init__(self, field_info, parent, remove_items: list[int] = None, open_on_show: bool = False):
        super().__init__(parent)
        self.table = parent
        self.field_info = field_info
        self.open_on_show = open_on_show

        # this parameter is mostly just a hacky thing to remove function resolutions
        self.remove_items = remove_items

    def createEditor(self, parent, option, index):
        widget = get_validated_input(self.field_info, parent)
        widget.editor.setParent(parent)
        widget.set_data(index.data(QtCore.Qt.ItemDataRole.DisplayRole))

        if self.remove_items is not None:
            for item in self.remove_items:
                widget.editor.removeItem(item)

        if self.open_on_show:
            widget.editor.open_on_show = True
            widget.editor.text_changed.connect(self.commit_and_close_editor)

        if issubclass(self.field_info.annotation, Enum):
            widget.editor.activated.connect(self.commit_and_close_editor)

        self.widget = widget
        # Using the BaseInputWidget directly did not style properly,
        # this uses the editor widget while holding a reference to BaseInputWidget.
        return widget.editor

    def commit_and_close_editor(self):
        editor = self.sender()
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)

    def setEditorData(self, _editor: QtWidgets.QWidget, index):
        data = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        extra = index.data(QtCore.Qt.ItemDataRole.UserRole)
        if extra:
            self.widget.editor.path = extra
        self.widget.set_data(data)

    def setModelData(self, _editor, model, index):
        data = self.widget.get_data()
        model.setData(index, data, QtCore.Qt.ItemDataRole.EditRole)


class CustomFileFunctionDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for choosing the function from a custom file."""

    def __init__(self, parent):
        super().__init__(parent)
        self.widget = parent

    def createEditor(self, parent, option, index):
        entry = index.siblingAtColumn(index.column() - 1)
        filename = entry.data(QtCore.Qt.ItemDataRole.DisplayRole)
        file_path = Path(entry.data(QtCore.Qt.ItemDataRole.UserRole)) / filename
        func_names = self.widget.model.get_function_names(file_path)
        # we define the methods set_data and get_data
        # so that setEditorData and setModelData don't need
        # to know what kind of widget the editor is
        if func_names is None:
            editor = QtWidgets.QLineEdit(parent)
            editor.set_data = editor.setText
            editor.get_data = editor.text
        else:
            editor = QtWidgets.QComboBox(parent)
            editor.addItems(func_names)
            editor.set_data = editor.setCurrentText
            editor.get_data = editor.currentText

        return editor

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

        widget.setMinimum(min_val)
        widget.setMaximum(max_val)

        # fill in background as otherwise you can see the original View text underneath
        widget.setAutoFillBackground(True)
        widget.setBackgroundRole(QtGui.QPalette.ColorRole.Base)
        widget.setButtonSymbols(QtWidgets.QSpinBox.ButtonSymbols.NoButtons)

        return widget

    def setEditorData(self, editor: AdaptiveDoubleSpinBox, index):
        data = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        editor.setValue(data)

    def setModelData(self, editor, model, index):
        data = editor.value()
        model.setData(index, data, QtCore.Qt.ItemDataRole.EditRole)


class ProjectFieldDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate to choose from existing draft project parameters."""

    def __init__(self, project_widget, field, parent, blank_option: bool = False):
        super().__init__(parent)
        self.field = field
        self.project_widget = project_widget
        self.blank_option = blank_option

    def createEditor(self, parent, option, index):
        widget = QtWidgets.QComboBox(parent, objectName="DelegateComboBox")
        parameters = self.project_widget.draft_project[self.field]
        names = [p.name for p in parameters]
        if self.blank_option:
            names = [""] + names
        widget.addItems(names)
        widget.setCurrentText(index.data(QtCore.Qt.ItemDataRole.DisplayRole))
        widget.currentTextChanged.connect(self.commit_and_close_editor)

        return widget

    def setEditorData(self, editor: QtWidgets.QWidget, index):
        data = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        editor.setCurrentText(data)

    def setModelData(self, editor, model, index):
        data = editor.currentText()
        model.setData(index, data, QtCore.Qt.ItemDataRole.EditRole)

    def commit_and_close_editor(self):
        editor = self.sender()
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)


class SignalSourceDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate to choose from draft project parameters, with a check for different source types."""

    def __init__(self, project_widget, parameter_field, parent):
        super().__init__(parent)
        self.parameter_field = parameter_field
        self.project_widget = project_widget
        self.parent = parent

    def createEditor(self, parent, option, index):
        match index.siblingAtColumn(index.column() - 1).data(QtCore.Qt.ItemDataRole.DisplayRole):
            case TypeOptions.Constant:
                field = self.parameter_field
            case TypeOptions.Data:
                field = "data"
            case TypeOptions.Function:
                field = "custom_files"
        editor_delegate = ProjectFieldDelegate(self.project_widget, field, self.parent)

        return editor_delegate.createEditor(parent, option, index)


class MultiSelectLayerDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for multiselecting layers."""

    def __init__(self, project_widget, parent):
        super().__init__(parent)
        self.project_widget = project_widget

    def createEditor(self, parent, option, index):
        widget = MultiSelectList(parent)

        layers = self.project_widget.draft_project["layers"]
        widget.update_selection_list([layer.name for layer in layers])

        return widget

    def setEditorData(self, editor: MultiSelectList, index):
        # index.data produces the display string rather than the underlying data,
        # so we split it back into a list here
        data = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        if data:
            data = data.split(", ")
            editor.list.clear()
            for item in data:
                editor.add_item(item)

    def setModelData(self, editor, model, index):
        data = [editor.list.item(i).text() for i in range(editor.list.count())]
        model.setData(index, data, QtCore.Qt.ItemDataRole.EditRole)
