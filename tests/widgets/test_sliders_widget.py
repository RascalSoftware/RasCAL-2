from unittest.mock import MagicMock, patch

import pydantic
import pytest
import ratapi
from matplotlib.widgets import Slider

from rascal2.ui.view import MainWindowView

from PyQt6 import QtWidgets, QtCore,QtGui

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

@pytest.fixture
def view_with_proj():
    """An instance of MainWindowView with project partially defined
       for mimicking sliders generation from project tabs
    """
    mw = MainWindowView()

    draft = create_draft_project(ratapi.Project())
    draft["parameters"] = ratapi.ClassList(
       [
                ratapi.models.Parameter(name="Param 1", min=1, max=10, value=2.1, fit=True),
                ratapi.models.Parameter(name="Param 2", min=10, max=100, value=20, fit=False),
                ratapi.models.Parameter(name="Param 3", min=100, max=1000, value=209, fit=True)
      ]
    )
    draft["background_parameters"] = ratapi.ClassList(
        [ratapi.models.Parameter(name="Background Param 1", min=0, max=1, value=0.2, fit=False),]
    )
    mw.project_widget.view_tabs["Parameters"].update_model(draft)
    mw.presenter.model.project = 1 # fake project to fool checks for project presence in GUI
    # without it normal project GUI will not be defined properly. Not used by SlidersWidget except
    # to check that project GUI is defined, assuming that if project is defined its GUI is also defined
    yield mw


def test_extract_properties_for_sliders(view_with_proj):

        update_sliders = view_with_proj.sliders_view_widget._init_properties_for_sliders()
        assert update_sliders == False # its false as at first call sliders should be regenerated
        assert len(view_with_proj.sliders_view_widget._prop_to_change) == 2
        assert list(view_with_proj.sliders_view_widget._prop_to_change.keys()) == ["Param 1", "Param 3"]
        assert list(view_with_proj.sliders_view_widget._values_to_revert.values()) == [2.1, 209.]
        assert view_with_proj.sliders_view_widget._init_properties_for_sliders() # now its true as sliders should be
        # available for update on second call


@patch("rascal2.ui.view.SlidersViewWidget._update_sliders_widgets")
@patch("rascal2.ui.view.SlidersViewWidget._add_sliders_widgets")
def test_create_update_called(add_sliders,update_sliders,view_with_proj):

    view_with_proj.sliders_view_widget.init()
    assert add_sliders.called == 1
    assert update_sliders.called == 0
    view_with_proj.sliders_view_widget.init()
    assert add_sliders.called == 1
    assert update_sliders.called == 1


def test_init_slider_widget_builds_sliders(view_with_proj):

    view_with_proj.sliders_view_widget.init()
    assert len(view_with_proj.sliders_view_widget._sliders) == 2
    assert "Param 1" in view_with_proj.sliders_view_widget._sliders
    assert "Param 3" in view_with_proj.sliders_view_widget._sliders
    slider1 = view_with_proj.sliders_view_widget._sliders["Param 1"]
    slider2 = view_with_proj.sliders_view_widget._sliders["Param 3"]
    assert slider1._prop._vis_model == view_with_proj.project_widget.view_tabs["Parameters"].tables["parameters"].model
    assert slider2._prop._vis_model == view_with_proj.project_widget.view_tabs["Parameters"].tables["parameters"].model


def fake_update(self,recalculate_project):
    fake_update.num_calls += 1
    fake_update.project_updated.append(recalculate_project)
fake_update.num_calls = 0
fake_update.project_updated = []

#@patch("rascal2.widgets.project.tables.ParameterFieldWidget.update_project")
@patch.object(ParameterFieldWidget,"update_project",fake_update)
def test_cancel_button_called(view_with_proj):

    view_with_proj.sliders_view_widget.init()
    view_with_proj.sliders_view_widget._values_to_revert['Param 1'] = 4
    view_with_proj.sliders_view_widget._values_to_revert['Param 3'] = 400
    cancel_button = view_with_proj.sliders_view_widget.findChild(QtWidgets.QPushButton,"CancelButton")

    cancel_button.click()

    assert fake_update.num_calls  == 2
    assert fake_update.project_updated  == [False, True]