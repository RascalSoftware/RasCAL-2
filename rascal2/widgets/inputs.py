"""Widget for validated user inputs."""
from enum import Enum
from math import floor, log10
from typing import Callable

from pydantic.fields import FieldInfo
from PyQt6 import QtCore, QtWidgets


class ValidatedInputWidget(QtWidgets.QWidget):
    """Number input for Pydantic field with validation."""

    def __init__(self, field_info: FieldInfo, parent=None):
        super().__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout()
        self.input_is_valid = True

        # editor_data and change_editor_data are set to the getter and setter
        # methods for the actual editor inside the widget
        self.editor_data: Callable
        self.change_editor_data: Callable
        self.edited_signal: QtCore.pyqtSignal

        # widget, getter, setter and change signal for different datatypes
        editor_types = {
            int: (QtWidgets.QSpinBox, "value", "setValue", "valueChanged"),
            float: (QtWidgets.QDoubleSpinBox, "value", "setValue", "valueChanged"),
            bool: (QtWidgets.QCheckBox, "isChecked", "setChecked", "checkStateChanged"),
        }
        defaults = (QtWidgets.QLineEdit, "text", "setText", "textChanged")

        if issubclass(field_info.annotation, Enum):
            self.editor = QtWidgets.QComboBox(self)
            self.editor.addItems(str(e.value) for e in field_info.annotation)
            self.editor_data = self.editor.currentText
            self.change_editor_data = self.editor.setCurrentText
            self.edited_signal = self.editor.currentTextChanged
        else:
            editor, getter, setter, signal = editor_types.get(field_info.annotation, defaults)
            self.editor = editor(self)
            self.editor_data = getattr(self.editor, getter)
            self.change_editor_data = getattr(self.editor, setter)
            self.edited_signal = getattr(self.editor, signal)
        if isinstance(self.editor, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
            set_constraints(self.editor, field_info)

        layout.addWidget(self.editor)

        self.validation_box = QtWidgets.QLabel()
        self.validation_box.setStyleSheet("QLabel { color : red; }")
        self.validation_box.font().setPointSize(10)
        self.validation_box.setWordWrap(True)
        layout.addWidget(self.validation_box)

        layout.setContentsMargins(5, 0, 0, 0)

        self.setLayout(layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)

    def set_validation_text(self, msg: str):
        """Write a message in the validation box.

        Parameters
        ----------
        msg: str
            The message to write in the validation box.
        """
        self.validation_box.setText(msg)
        if msg != "":
            self.editor.setStyleSheet("color : red")
            self.input_is_valid = False
        else:
            self.editor.setStyleSheet("")
            self.input_is_valid = True


def set_constraints(widget: QtWidgets.QSpinBox | QtWidgets.QDoubleSpinBox, field_info) -> None:
    metadata = field_info.metadata
    if isinstance(widget, QtWidgets.QDoubleSpinBox):
        widget.setStepType(widget.StepType.AdaptiveDecimalStepType)
        if hasattr(field_info, "default") and field_info.default > 0:
            # set decimals to order of magnitude of default value
            widget.setDecimals(-floor(log10(abs(field_info.default))))
    for item in metadata:
        # using a 'guessing attributes' method rather than importing the annotation classes
        # which would add a dependency since they're from the annotated_types package
        for attr in ["ge", "gt"]:
            if hasattr(item, attr):
                widget.setMinimum(getattr(item, attr))
        for attr in ["le", "lt"]:
            if hasattr(item, attr):
                widget.setMaximum(getattr(item, attr))
