from PyQt6 import QtCore

from rascal2.dialogs.startup_dialog import ProjectDialog, StartUpDialog


def test_startup_dialog_initial_state():
    """
    Tests the initial state of the start up dialog.
    """
    startup_dialog = StartUpDialog()

    assert startup_dialog.windowFlags() == (QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Dialog)
    assert startup_dialog.isModal()

    assert startup_dialog._new_project_button.isEnabled()
    assert startup_dialog._import_project_button.isEnabled()
    assert startup_dialog._load_example_button.isEnabled()

    assert startup_dialog._new_project_label.text() == "New\nProject"
    assert startup_dialog._import_project_label.text() == "Import Existing\nProject"
    assert startup_dialog._load_example_label.text() == "Open Example\nProject"


def test_project_dialog_initial_state():
    """
    Tests the inital state of the project dialog.
    """
    project_dialog = ProjectDialog()

    assert project_dialog.isModal()

    assert project_dialog._create_button.isEnabled()
    assert project_dialog._cancel_button.isEnabled()
    assert project_dialog._browse_button.isEnabled()

    assert project_dialog._create_button.text() == " Create"
    assert project_dialog._cancel_button.text() == " Cancel"
    assert project_dialog._browse_button.text() == " Browse"

    assert project_dialog._project_name_label.text() == "Project Name:"
    assert project_dialog._project_folder_label.text() == "Project Folder:"
    assert project_dialog._project_folder.text() == "No folder selected"

    assert project_dialog._project_name.text() == ""
    assert project_dialog._project_name.placeholderText() == "Enter project name"
    assert not project_dialog._folder_selected
