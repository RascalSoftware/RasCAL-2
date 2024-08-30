from PyQt6 import QtCore

from rascal2.dialogs.project_dialog import ProjectDialog


def test_project_dialog_initial_state():
    """
    Tests the inital state of the project dialog.
    """
    project_dialog = ProjectDialog()

    assert project_dialog.windowFlags() == (QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Dialog)

    assert project_dialog.isModal()

    assert project_dialog.create_button.isEnabled()
    assert project_dialog.cancel_button.isEnabled()
    assert project_dialog.browse_button.isEnabled()

    assert project_dialog.create_button.text() == " Create"
    assert project_dialog.cancel_button.text() == " Cancel"
    assert project_dialog.browse_button.text() == " Browse"

    assert project_dialog.project_name_label.text() == "Project Name:"
    assert project_dialog.project_folder_label.text() == "Project Folder:"
    assert project_dialog.project_folder.text() == "No folder selected"

    assert project_dialog.project_name.text() == ""
    assert project_dialog.project_name.placeholderText() == "Enter project name"
    assert not project_dialog.folder_selected
