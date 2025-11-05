from unittest.mock import MagicMock, patch

import pytest
import ratapi
from PyQt6 import QtWidgets

from rascal2.widgets.sliders_view import (
    SlidersViewWidget,
    LabeledSlider
)
@pytest.fixture
def slider():
    param = ratapi.models.Parameter(name = "Test Slider", min=1, max=10, value = 2.1, fit=True)
    return LabeledSlider(param)


def test_a_slider_construction(slider):
    """constructing a slider widget works and have all necessary properties"""
    assert slider.slider_name == "Test Slider"
    assert slider._value_min == 1
    assert slider._value_range == 10-1
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


