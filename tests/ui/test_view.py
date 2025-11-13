"""Unit tests for the main window view."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PyQt6 import QtWidgets

from rascal2.settings import MDIGeometries, Settings
from rascal2.ui.view import MainWindowView


class MockFigureCanvas(QtWidgets.QWidget):
    """A mock figure canvas."""

    def draw(*args, **kwargs):
        pass


class MockNavigationToolbar(QtWidgets.QWidget):
    """A mock navigation toolbar."""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._actions = {"pan": None, "zoom": None}


@pytest.fixture
def test_view():
    """An instance of MainWindowView."""
    with (
        patch("rascal2.widgets.plot.FigureCanvasQTAgg", return_value=MockFigureCanvas()),
        patch("rascal2.widgets.plot.NavigationToolbar2QT", return_value=MockNavigationToolbar()),
    ):
        yield MainWindowView()


@pytest.mark.parametrize(
    "geometry",
    [
        (
            (1, 2, 196, 24, True),
            (1, 2, 196, 24, True),
            (1, 2, 196, 24, True),
            (1, 2, 196, 24, True),
            (1, 2, 196, 24, True),
        ),
        (
            (1, 2, 196, 24, True),
            (3, 78, 196, 24, True),
            (1, 2, 204, 66, False),
            (12, 342, 196, 24, True),
            (5, 6, 200, 28, True),
        ),
    ],
)
@patch("rascal2.ui.view.ProjectWidget.show_project_view")
@patch("rascal2.ui.view.MainWindowPresenter")
@patch("rascal2.ui.view.ControlsWidget.setup_controls")
class TestMDISettings:
    def test_reset_mdi(self, mock1, mock2, mock3, test_view, geometry):
        """Test that resetting the MDI works."""
        test_view.settings = Settings()
        test_view.setup_mdi()
        test_view.settings.mdi_defaults = MDIGeometries(
            Plots=geometry[0],
            Project=geometry[1],
            Terminal=geometry[2],
            FittingControls=geometry[3],
            SlidersView=geometry[4],
        )
        test_view.reset_mdi_layout()
        for window in test_view.mdi.subWindowList():
            # get corresponding MDIGeometries entry for the widget
            widget_name = window.windowTitle().replace(" ", "")
            w_geom = window.geometry()
            assert getattr(test_view.settings.mdi_defaults, widget_name) == (
                w_geom.x(),
                w_geom.y(),
                w_geom.width(),
                w_geom.height(),
                window.isMinimized(),
            )

    def test_set_mdi(self, mock1, mock2, mock3, test_view, geometry):
        """Test that setting the MDI adds the expected object to settings."""
        test_view.settings = Settings()
        test_view.setup_mdi()
        widgets_in_order = []

        for i, window in enumerate(test_view.mdi.subWindowList()):
            widgets_in_order.append(window.windowTitle().replace(" ", ""))
            window.setGeometry(*geometry[i][0:4])
            if geometry[i][4] is True:
                window.showMinimized()

        test_view.save_mdi_layout()
        for i, widget in enumerate(widgets_in_order):
            window = test_view.mdi.subWindowList()[i]
            assert getattr(test_view.settings.mdi_defaults, widget) == (
                window.x(),
                window.y(),
                window.width(),
                window.height(),
                window.isMinimized(),
            )


def test_set_enabled(test_view):
    """Tests that the list of disabled elements are disabled on initialisation, and can be enabled."""
    for element in test_view.disabled_elements:
        assert not element.isEnabled()
    test_view.enable_elements()
    for element in test_view.disabled_elements:
        assert element.isEnabled()


@patch("PyQt6.QtWidgets.QFileDialog.getExistingDirectory")
def test_get_project_folder(mock_get_dir: MagicMock):
    """Test that getting a specified folder works as expected."""
    view = MainWindowView()
    mock_overwrite = MagicMock(return_value=True)

    tmp = tempfile.mkdtemp()
    view.presenter.create_project("test", tmp)
    mock_get_dir.return_value = tmp

    with patch.object(view, "show_confirm_dialog", new=mock_overwrite):
        assert view.get_project_folder() == tmp

    # check overwrite is triggered if project already in folder
    Path(tmp, "controls.json").touch()
    with patch.object(view, "show_confirm_dialog", new=mock_overwrite):
        assert view.get_project_folder() == tmp
    mock_overwrite.assert_called_once()

    def change_dir(*args, **kwargs):
        """Change directory so mocked save_as doesn't recurse forever."""
        mock_get_dir.return_value = "OTHERPATH"

    # check not saved if overwrite is cancelled
    # to avoid infinite recursion (which only happens because of the mock),
    # set the mock to change the directory to some other path once called
    mock_overwrite = MagicMock(return_value=False, side_effect=change_dir)

    with patch.object(view, "show_confirm_dialog", new=mock_overwrite):
        assert view.get_project_folder() == "OTHERPATH"

    mock_overwrite.assert_called_once()


@pytest.mark.parametrize("submenu_name", ["&File", "&Edit", "&Windows", "&Tools", "&Help"])
def test_menu_element_present(test_view, submenu_name):
    """Test requested menu items are present"""

    main_menu = test_view.menuBar()

    elements = main_menu.children()
    assert any(hasattr(submenu, "title") and submenu.title() == submenu_name for submenu in elements)


@pytest.mark.parametrize(
    "submenu_name, action_names_and_layout",
    [
        (
            "&File",
            [
                "&New Project",
                "",
                "&Open Project",
                "Open &RasCAL-1 Project",
                "",
                "&Save",
                "Save To &Folder...",
                "",
                "Export Results",
                "",
                "Settings",
                "",
                "E&xit",
            ],
        ),
        ("&Edit", ["&Undo", "&Redo", "Undo &History"]),
        ("&Windows", ["Tile Windows", "Reset to Default", "Save Current Window Positions"]),
        ("&Tools", ["&Show Sliders", "", "Clear Terminal", "", "Setup MATLAB"]),
        ("&Help", ["&About", "&Help"]),
    ],
)
def test_help_menu_actions_present(test_view, submenu_name, action_names_and_layout):
    """Test if menu actions are available and their layouts are as specified in parameterize"""

    main_menu = test_view.menuBar()
    submenu = main_menu.findChild(QtWidgets.QMenu, submenu_name)
    actions = submenu.actions()
    assert len(actions) == len(action_names_and_layout)
    for action, name in zip(actions, action_names_and_layout, strict=True):
        assert action.text() == name


@pytest.fixture
def test_view_with_mdi():
    """An instance of MainWindowView with mdi property defined to some rubbish
    for mimicking operations performed in MainWindowView.reset_mdi_layout
    """
    with patch("rascal2.widgets.plot.FigureCanvas", return_value=MockFigureCanvas()):
        mw = MainWindowView()
        mw.mdi.addSubWindow(mw.sliders_view_widget)
        mdi_windows = mw.mdi.subWindowList()
        mw.sliders_view_widget.mdi_holder = mdi_windows[0]
        mw.enable_elements()
        yield mw


@patch("rascal2.ui.view.SlidersViewWidget.show")
@patch("rascal2.ui.view.SlidersViewWidget.hide")
def test_click_on_select_sliders_works_as_expected(mock_hide, mock_show, test_view_with_mdi):
    """Test if click on menu in the state "Show Slider" changes text appropriately
    and initiates correct callback
    """

    # check initial state -- defined now but needs to be refactored when
    # this may be included in configuration
    assert not test_view_with_mdi.show_sliders

    main_menu = test_view_with_mdi.menuBar()
    submenu = main_menu.findChild(QtWidgets.QMenu, "&Tools")
    all_actions = submenu.actions()

    # Trigger the action
    all_actions[0].trigger()
    assert all_actions[0].text() == "&Hide Sliders"
    assert test_view_with_mdi.show_sliders
    assert mock_show.call_count == 1


@patch("rascal2.ui.view.SlidersViewWidget.show")
@patch("rascal2.ui.view.SlidersViewWidget.hide")
def test_click_on_select_tabs_works_as_expected(mock_hide, mock_show, test_view_with_mdi):
    """Test if click on menu in the state "Show Sliders" changes text appropriately
    and initiates correct callback
    """

    # check initial state -- defined now but needs to be refactored when
    # this may be included in configuration
    assert not test_view_with_mdi.show_sliders

    main_menu = test_view_with_mdi.menuBar()
    submenu = main_menu.findChild(QtWidgets.QMenu, "&Tools")
    all_actions = submenu.actions()

    # Trigger the action
    all_actions[0].trigger()
    assert test_view_with_mdi.show_sliders
    assert mock_show.call_count == 1  # this would show sliders widget
    # check if next click returns to initial state
    all_actions[0].trigger()

    assert all_actions[0].text() == "&Show Sliders"
    assert not test_view_with_mdi.show_sliders
    assert mock_hide.call_count == 1  # this would hide sliders widget
