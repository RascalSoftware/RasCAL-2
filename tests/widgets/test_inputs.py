"""Test input widgets."""

try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum
import os
from pathlib import Path

import pytest
from pydantic.fields import FieldInfo
from PyQt6 import QtWidgets

from rascal2.widgets import (
    AdaptiveDoubleSpinBox,
    MultiSelectComboBox,
    MultiSelectList,
    PathWidget,
    ProgressButton,
    get_validated_input,
)


class MyEnum(StrEnum):
    VALUE_1 = "value 1"
    VALUE_2 = "value 2"
    VALUE_3 = "value 3"


@pytest.mark.parametrize(
    ("field_info", "expected_type", "example_data"),
    [
        (FieldInfo(annotation=bool), QtWidgets.QCheckBox, True),
        (FieldInfo(annotation=float), AdaptiveDoubleSpinBox, 11.5),
        (FieldInfo(annotation=int), QtWidgets.QSpinBox, 15),
        (FieldInfo(annotation=MyEnum), QtWidgets.QComboBox, "value 2"),
        (FieldInfo(annotation=str), QtWidgets.QLineEdit, "Test string"),
        (FieldInfo(annotation=Path), PathWidget, Path(".").resolve().as_posix()),
    ],
)
def test_editor_type(field_info, expected_type, example_data):
    """Test that the editor type is as expected, and can be read and written."""
    widget = get_validated_input(field_info)
    assert isinstance(widget.editor, expected_type)
    widget.set_data(example_data)
    assert widget.get_data() == example_data


@pytest.mark.parametrize("selected", ([], [1], [0, 2]))
def test_multi_select_combo_update(selected):
    """Test that the selected data updates correctly."""
    combobox = MultiSelectComboBox()
    assert combobox.lineEdit().text() == ""
    assert combobox.selected_items() == []
    items = ["A", "B", "C"]
    combobox.addItems(items)

    combobox.select_indices(selected)
    expected_items = [items[i] for i in selected]
    assert combobox.selected_items() == expected_items
    assert combobox.lineEdit().text() == ", ".join(expected_items)


@pytest.mark.parametrize("selected", ([], [1], [0, 2]))
def test_multi_select_list_update(selected):
    """Test that the selected data updates correctly."""
    msl = MultiSelectList()
    assert msl.select_menu.actions() == []
    assert msl.list.selectedItems() == []
    items = ["A", "B", "C"]
    msl.update_selection_list(items)

    actions = msl.select_menu.actions()
    expected_items = []
    for i in selected:
        actions[i].trigger()
        expected_items.append(items[i])
        msl.list.item(msl.list.count() - 1).setSelected(True)

    assert expected_items == [msl.list.item(i).text() for i in range(msl.list.count())]
    buttons = msl.findChildren(QtWidgets.QToolButton)
    buttons[1].click()
    assert msl.list.count() == 0


def test_path_widget():
    widget = PathWidget(None)
    assert widget.path == os.getcwd()
    assert widget.text() == Path(widget.path).as_posix()

    path = Path(".") / "file.m"
    widget.setText(path)
    assert widget.path == path.parent.as_posix()
    assert widget.text() == path.name


def test_progress_button():
    widget = ProgressButton("Progress", "Testing button")

    assert widget.text() == "Progress"
    widget.default_text = "Start"
    assert widget.text() == "Start"

    widget.click()
    assert not widget.isEnabled()
    assert widget.text() == "Testing button ..."

    widget.update_progress(1, 2)
    assert not widget.isEnabled()
    assert widget.text() == "Testing button - 1 of 2"

    widget.hide_progress()
    assert widget.isEnabled()
    assert widget.text() == "Start"
