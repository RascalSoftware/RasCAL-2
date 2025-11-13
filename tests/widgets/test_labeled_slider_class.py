from unittest.mock import MagicMock, patch

import pydantic
import pytest
import ratapi

from PyQt6 import QtWidgets, QtCore

from rascal2.widgets.sliders_view import (
    SliderChangeHolder,
    LabeledSlider
)
from rascal2.widgets.project.tables import (
    ParametersModel
)


class ParametersModelMock(ParametersModel):

    _value: float
    _index: QtCore.QModelIndex
    _role: QtCore.Qt.ItemDataRole
    _recalculate_proj: bool
    call_count: int

    def __init__(self, class_list: ratapi.ClassList, parent: QtWidgets.QWidget):
        super().__init__(class_list, parent)
        self.call_count  = 0

    def setData(self,index : QtCore.QModelIndex, val : float, qt_role = QtCore.Qt.ItemDataRole.EditRole,recalculate_project = True) -> bool:
        self._index = index
        self._value = val
        self._role = qt_role
        self._recalculate_proj = recalculate_project
        self.call_count+=1
        return True

class DataModel(pydantic.BaseModel, validate_assignment=True):
    """A test Pydantic model."""

    name: str
    min: float
    max: float
    value: float
    fit: bool
    show_priors: bool


@pytest.fixture
def slider():
    param = ratapi.models.Parameter(name = "Test Slider", min=1, max=10, value = 2.1, fit=True)
    parent = QtWidgets.QWidget()
    class_view = ratapi.ClassList(
        [
            DataModel(name="Slider_A", min = 0,value=1,max=100,fit=True,show_priors = False),
            DataModel(name="Slider_B", min = 0, value=1, max=100, fit=True, show_priors=False),
            DataModel(name="Slider_C", min = 0, value=1, max=100, fit=True, show_priors=False),
        ]
    )
    model = ParametersModelMock(class_view, parent)
    # note 3 elements in ratapi.ClassList for row_number == 2 to work
    inputs = SliderChangeHolder(row_number=2,model=model, param=param)
    return LabeledSlider(inputs)


def test_a_slider_construction(slider):
    """constructing a slider widget works and have all necessary properties"""
    assert slider.slider_name == "Test Slider"
    assert slider._value_min == 1
    assert slider._value_range == 10-1
    assert slider._value == 2.1
    assert slider._value_step == 9/100
    assert len(slider._labels) == 11

def test_a_slider_label_range(slider):
    """check if labels cover whole property range"""
    assert len(slider._labels) == 11
    assert slider._labels[0].text() == slider._tick_label_format.format(1)
    assert slider._labels[-1].text() == slider._tick_label_format.format(10)

def test_a_slider_value_text(slider):
    """check if slider have correct value label"""
    assert slider._value_label.text() == slider._value_label_format.format(2.1)

def test_set_slider_value_changes_label(slider):
    """check if slider accepts correct value and uses correct index"""
    slider.set_slider_gui_position(4)
    assert slider._value_label.text() == slider._value_label_format.format(4)
    idx = slider._value_to_slider_pos(4)
    assert slider._slider.value() == idx

def test_set_slider_max_value_in_range(slider):
    """ round-off error keep sliders within the ranges"""
    slider.set_slider_gui_position(slider._value_max)
    assert slider._value_label.text() == slider._value_label_format.format(slider._value_max)
    assert slider._slider.value() == slider._slider_max_idx

def test_set_slider_min_value_in_range(slider):
    """ round-off error keep sliders within the ranges"""
    slider.set_slider_gui_position(slider._value_min)
    assert slider._value_label.text() == slider._value_label_format.format(slider._value_min)
    assert slider._slider.value() == 0

def test_set_value_do_correct_calls(slider):
    """ update value bound correctly and does correct calls """

    assert slider._prop._vis_model.call_count == 0
    slider._slider.setValue(50)
    float_val = slider._slider_pos_to_value(50)
    assert float_val == slider._value
    assert slider._slider.value() == 50
    assert slider._prop._vis_model.call_count == 1
    assert slider._prop._vis_model._value == float_val
    assert slider._prop._vis_model._index.row() == 2 # row number in slider fixture
    assert slider._prop._vis_model._role ==  QtCore.Qt.ItemDataRole.EditRole # row number in slider fixture

@pytest.mark.parametrize(
    "minmax_slider_idx, min_max_prop_value",
    [
    (0, 1),  # min_max indices are the indices hardwired in class and
    (100, 10), # min_max values are the values supplied for property in the slider fixture
    ]
)
def test_set_values_in_limits_work(slider, minmax_slider_idx, min_max_prop_value):
    """ update_value bound correctly and does correct calls at limiting values"""

    slider._slider.setValue(minmax_slider_idx)
    assert min_max_prop_value == slider._value
    assert slider._slider.value() == minmax_slider_idx
    assert slider._value  == min_max_prop_value
    assert slider._prop._vis_model._value == min_max_prop_value
    assert slider._prop.param.value == min_max_prop_value
