from unittest.mock import patch

import pytest

from rascal2.widgets.startup_widget import StartUpWidget
from tests.test_dialogs import MockParentWindow


@pytest.fixture
def setup_startup_widget():
    parent = MockParentWindow()
    startup_widget = StartUpWidget(parent)
    return startup_widget, parent


def test_startup_widget_initial_state(setup_startup_widget):
    """
    Tests the initial state of the start up widget.
    """
    startup_widget, _ = setup_startup_widget
    assert startup_widget.new_project_button.isEnabled()
    assert startup_widget.import_project_button.isEnabled()
    assert startup_widget.import_r1_button.isEnabled()

    assert startup_widget.new_project_label.text() == "New\nProject"
    assert startup_widget.import_project_label.text() == "Import Existing\nProject"
    assert startup_widget.import_r1_label.text() == "Import RasCAL-1\nProject"


@patch.object(MockParentWindow, "toggleView")
def test_toggle_view_called(mock, setup_startup_widget):
    """
    Tests the toggleView method is called once.
    """
    startup_widget, _ = setup_startup_widget
    startup_widget.new_project_button.click()
    mock.assert_called_once()
