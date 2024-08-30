from rascal2.ui.view import MainWindowView
from rascal2.widgets.startup_widget import StartUpWidget


def test_startup_widget_initial_state():
    """
    Tests the initial state of the start up widget.
    """
    view = MainWindowView()
    startup_widget = StartUpWidget(view)

    assert startup_widget.new_project_button.isEnabled()
    assert startup_widget.import_project_button.isEnabled()
    assert startup_widget.load_example_button.isEnabled()
    assert startup_widget.import_r1_button.isEnabled()
    assert startup_widget.cancel_button.isEnabled()
    assert startup_widget.import_rascal_button.isEnabled()

    assert startup_widget.new_project_label.text() == "New\nProject"
    assert startup_widget.import_project_label.text() == "Import Existing\nProject"
    assert startup_widget.load_example_label.text() == "Open Example\nProject"
    assert startup_widget.import_r1_label.text() == "Import R1\nProject"
    assert startup_widget.cancel_label.text() == "Cancel"
    assert startup_widget.import_rascal_label.text() == "Import RasCAL\nProject"
