from unittest.mock import MagicMock, patch

import pydantic
import pytest
import ratapi

from PyQt6 import QtWidgets, QtCore

from rascal2.widgets.sliders_view import (
    SlidersViewWidget,
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
            DataModel(name="Slider_B", min = 0, value=6,max = 200,fit=True,show_priors = False),
            DataModel(name="Slider_C", min = 0,value=18,max=300,fit=True,show_priors = False)
        ]
    )
    model = ParametersModelMock(class_view, parent)
    inputs = SliderChangeHolder(row_number=2,model=model, param=param)
    return LabeledSlider(inputs)
