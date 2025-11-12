from unittest.mock import MagicMock, patch

import pydantic
import pytest
import ratapi
from rascal2.ui.view import MainWindowView

from PyQt6 import QtWidgets, QtCore

from rascal2.widgets.project.project import create_draft_project
from rascal2.widgets.sliders_view import (
    SlidersViewWidget,
    SliderChangeHolder,
    LabeledSlider
)
from rascal2.widgets.project.tables import (
    ParameterFieldWidget,
    ParametersModel
)
class MockFigureCanvas(QtWidgets.QWidget):
    """A mock figure canvas."""

    def draw(*args, **kwargs):
        pass

#@pytest.fixture
def test_view_with_project():
    """An instance of MainWindowView with mdi property defined to some rubbish
       for mimicking operations performed in MainWindowView.reset_mdi_layout
    """
    #with patch("rascal2.widgets.plot.FigureCanvas", return_value=MockFigureCanvas()):
    mw = MainWindowView()

    draft = create_draft_project(ratapi.Project())
    draft["parameters"] = ratapi.ClassList(
        [
            ratapi.models.Parameter(name="Param 1", min=1, max=10, value=2.1, fit=True),
            ratapi.models.Parameter(name="Param 2", min=10, max=100, value=20, fit=False),
            ratapi.models.Parameter(name="Param 3", min=100, max=1000, value=209, fit=True)
        ]
    )
    mw.project_widget.view_tabs["Parameters"].update_model(draft)
        #yield mw
    return mw


def test_extract_properties_for_sliders():
        tw = test_view_with_project()
        update_sliders = tw.sliders_view_widget._init_properties_for_sliders()
        assert update_sliders == False # its false as at first call sliders should be regenerated
        assert len(tw.sliders_view_widget._prop_to_change) == 2
        assert list(tw.sliders_view_widget._prop_to_change.keys()) == ["Param 1", "Param 3"]
        assert list(tw.sliders_view_widget._values_to_revert.values()) == [2.1, 209.]
        assert tw.sliders_view_widget._init_properties_for_sliders() # not its true as sliders should be available
        # for update on second call
