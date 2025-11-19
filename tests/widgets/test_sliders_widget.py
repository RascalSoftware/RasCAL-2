from unittest.mock import patch

import pytest
import ratapi
from PyQt6 import QtWidgets

from rascal2.ui.view import MainWindowView
from rascal2.widgets.project.project import ProjectWidget, create_draft_project
from rascal2.widgets.project.tables import ParameterFieldWidget
from rascal2.widgets.sliders_view import EmptySlider, LabeledSlider, SlidersViewWidget


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
            ratapi.models.Parameter(name="Param 3", min=100, max=1000, value=209, fit=True),
            ratapi.models.Parameter(name="Param 4", min=200, max=2000, value=409, fit=True),
        ]
    )
    draft["background_parameters"] = ratapi.ClassList(
        [
            ratapi.models.Parameter(name="Background Param 1", min=0, max=1, value=0.2, fit=False),
        ]
    )
    project = ratapi.Project(name="Sliders Test Project")
    for param in draft["parameters"]:
        project.parameters.append(param)
    for param in draft["background_parameters"]:
        project.parameters.append(param)

    mw.project_widget.view_tabs["Parameters"].update_model(draft)
    mw.presenter.model.project = project

    yield mw


def test_extract_properties_for_sliders(view_with_proj):
    update_sliders = view_with_proj.sliders_view_widget._init_properties_for_sliders()
    assert not update_sliders  # its false as at first call sliders should be regenerated
    assert len(view_with_proj.sliders_view_widget._prop_to_change) == 3
    assert list(view_with_proj.sliders_view_widget._prop_to_change.keys()) == ["Param 1", "Param 3", "Param 4"]
    assert list(view_with_proj.sliders_view_widget._values_to_revert.values()) == [2.1, 209.0, 409]
    assert view_with_proj.sliders_view_widget._init_properties_for_sliders()  # now its true as sliders should be
    # available for update on second call


@patch("rascal2.ui.view.SlidersViewWidget._update_sliders_widgets")
@patch("rascal2.ui.view.SlidersViewWidget._add_sliders_widgets")
def test_create_update_called(add_sliders, update_sliders, view_with_proj):
    view_with_proj.sliders_view_widget.init()
    assert add_sliders.called == 1
    assert update_sliders.called == 0
    view_with_proj.sliders_view_widget.init()
    assert add_sliders.called == 1
    assert update_sliders.called == 1


def test_init_slider_widget_builds_sliders(view_with_proj):
    view_with_proj.sliders_view_widget.init()
    assert len(view_with_proj.sliders_view_widget._sliders) == 3
    assert "Param 1" in view_with_proj.sliders_view_widget._sliders
    assert "Param 3" in view_with_proj.sliders_view_widget._sliders
    assert "Param 4" in view_with_proj.sliders_view_widget._sliders
    slider1 = view_with_proj.sliders_view_widget._sliders["Param 1"]
    slider2 = view_with_proj.sliders_view_widget._sliders["Param 3"]
    slider3 = view_with_proj.sliders_view_widget._sliders["Param 4"]
    assert slider1._prop._vis_model == view_with_proj.project_widget.view_tabs["Parameters"].tables["parameters"].model
    assert slider2._prop._vis_model == view_with_proj.project_widget.view_tabs["Parameters"].tables["parameters"].model
    assert slider3._prop._vis_model == view_with_proj.project_widget.view_tabs["Parameters"].tables["parameters"].model


def fake_update(self, recalculate_project):
    fake_update.num_calls += 1
    fake_update.project_updated.append(recalculate_project)


fake_update.num_calls = 0
fake_update.project_updated = []


def test_identify_changed_properties_empty_for_unchanged(view_with_proj):
    view_with_proj.sliders_view_widget.init()

    assert len(view_with_proj.sliders_view_widget._identify_changed_properties()) == 0


def test_identify_changed_properties_picks_up_changed(view_with_proj):
    view_with_proj.sliders_view_widget.init()
    view_with_proj.sliders_view_widget._values_to_revert["Param 1"] = 4
    view_with_proj.sliders_view_widget._values_to_revert["Param 3"] = 400

    assert len(view_with_proj.sliders_view_widget._identify_changed_properties()) == 2
    assert list(view_with_proj.sliders_view_widget._identify_changed_properties().keys()) == ["Param 1", "Param 3"]


@patch.object(ParameterFieldWidget, "update_project", fake_update)
@patch("rascal2.ui.view.ProjectWidget.show_project_view")
def test_cancel_button_called(mock_show_project, view_with_proj):
    """Cancel button sets value of controlled properties to value, stored in
    _value_to_revert dictionary
    """

    view_with_proj.sliders_view_widget.init()

    view_with_proj.sliders_view_widget._values_to_revert["Param 1"] = 4
    view_with_proj.sliders_view_widget._values_to_revert["Param 3"] = 400
    cancel_button = view_with_proj.sliders_view_widget.findChild(QtWidgets.QPushButton, "CancelButton")

    cancel_button.click()

    assert fake_update.num_calls == 2
    # project update should be true for last property change
    assert fake_update.project_updated == [False, True]
    assert not view_with_proj.show_sliders
    assert view_with_proj.presenter.model.project.parameters["Param 1"].value == 4
    assert view_with_proj.presenter.model.project.parameters["Param 2"].value == 20
    assert view_with_proj.presenter.model.project.parameters["Param 3"].value == 400
    assert view_with_proj.presenter.model.project.parameters["Param 4"].value == 409

    assert mock_show_project.call_count == 1


@patch("rascal2.ui.view.SlidersViewWidget._apply_changes_from_sliders")
def test_cancel_accept_button_connections(mock_accept, view_with_proj):
    view_with_proj.sliders_view_widget.init()

    accept_button = view_with_proj.sliders_view_widget.findChild(QtWidgets.QPushButton, "AcceptButton")
    accept_button.clicked.disconnect()  # previous actual function was connected regardless
    accept_button.clicked.connect(view_with_proj.sliders_view_widget._apply_changes_from_sliders)
    accept_button.click()
    assert mock_accept.called == 1


@patch("rascal2.ui.view.SlidersViewWidget._cancel_changes_from_sliders")
def test_cancel_cancel_button_connections(mock_cancel, view_with_proj):
    view_with_proj.sliders_view_widget.init()
    cancel_button = view_with_proj.sliders_view_widget.findChild(QtWidgets.QPushButton, "CancelButton")
    cancel_button.clicked.disconnect()  # previous actual function was connected regardless
    cancel_button.clicked.connect(view_with_proj.sliders_view_widget._cancel_changes_from_sliders)

    cancel_button.click()
    assert mock_cancel.called == 1


def fake_show_or_hide_sliders(self, do_show_sliders):
    fake_show_or_hide_sliders.num_calls = +1
    fake_show_or_hide_sliders.call_param = do_show_sliders


fake_show_or_hide_sliders.num_calls = 0
fake_show_or_hide_sliders.call_param = []


@patch.object(MainWindowView, "show_or_hide_sliders", fake_show_or_hide_sliders)
def test_apply_cancel_changes_called_hide_sliders(view_with_proj):
    view_with_proj.sliders_view_widget._cancel_changes_from_sliders()
    assert fake_show_or_hide_sliders.num_calls == 1
    assert not fake_show_or_hide_sliders.call_param

    fake_show_or_hide_sliders.num_calls = 0
    fake_show_or_hide_sliders.call_param = []

    view_with_proj.sliders_view_widget._apply_changes_from_sliders()
    assert fake_show_or_hide_sliders.num_calls == 1
    assert not fake_show_or_hide_sliders.call_param


# ======================================================================================================================
def set_proj_properties_fit_to_requested(proj, true_list: list):
    """set up all projects properties "fit" parameter to False except provided
    within the true_list, which to be set to True"""

    project = proj.presenter.model.project
    for field in ratapi.Project.model_fields:
        attr = getattr(project, field)
        if isinstance(attr, ratapi.ClassList):
            for item in attr:
                if hasattr(item, "fit"):
                    if item.name in true_list:
                        item.fit = True
                    else:
                        item.fit = False


def test_empty_slider_generated(view_with_proj):
    set_proj_properties_fit_to_requested(view_with_proj, [])

    view_with_proj.sliders_view_widget.init()
    assert len(view_with_proj.sliders_view_widget._sliders) == 1
    slider1 = view_with_proj.sliders_view_widget._sliders["Empty Slider"]
    assert isinstance(slider1, EmptySlider)


def test_empty_slider_updated(view_with_proj):
    set_proj_properties_fit_to_requested(view_with_proj, [])

    view_with_proj.sliders_view_widget.init()
    assert len(view_with_proj.sliders_view_widget._sliders) == 1
    slider1 = view_with_proj.sliders_view_widget._sliders["Empty Slider"]
    assert isinstance(slider1, EmptySlider)
    view_with_proj.sliders_view_widget.init()
    assert isinstance(slider1, EmptySlider)


def test_empty_slider_removed(view_with_proj):
    set_proj_properties_fit_to_requested(view_with_proj, [])

    view_with_proj.sliders_view_widget.init()
    assert len(view_with_proj.sliders_view_widget._sliders) == 1
    slider1 = view_with_proj.sliders_view_widget._sliders["Empty Slider"]
    assert isinstance(slider1, EmptySlider)

    set_proj_properties_fit_to_requested(view_with_proj, ["Param 2"])

    view_with_proj.sliders_view_widget.init()
    assert len(view_with_proj.sliders_view_widget._sliders) == 1
    slider1 = view_with_proj.sliders_view_widget._sliders["Param 2"]
    assert isinstance(slider1, LabeledSlider)
