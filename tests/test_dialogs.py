from unittest.mock import patch

import pytest
from PyQt6 import QtCore, QtTest, QtWidgets

from rascal2.dialogs.project_dialog import ProjectDialog


class MockParentWindow(QtWidgets.QMainWindow):
    new_project_action_called = False

    def toggleView(self):
        pass

    def createNewProject(self):
        pass


@pytest.fixture
def setup_project_dialog_widget():
    parent = MockParentWindow()
    project_dialog = ProjectDialog(parent)
    return project_dialog, parent


def test_project_dialog_initial_state(setup_project_dialog_widget):
    """
    Tests the inital state of the project dialog.
    """
    project_dialog, _ = setup_project_dialog_widget

    assert project_dialog.windowFlags() == (QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Dialog)

    assert project_dialog.isModal()
    assert project_dialog.minimumWidth() == 700

    assert project_dialog.create_button.isEnabled()
    assert project_dialog.cancel_button.isEnabled()
    assert project_dialog.browse_button.isEnabled()

    assert project_dialog.create_button.text() == " Create"
    assert project_dialog.cancel_button.text() == " Cancel"
    assert project_dialog.browse_button.text() == " Browse"

    assert project_dialog.project_name.placeholderText() == "Enter project name"
    assert project_dialog.project_name_label.text() == "Project Name:"
    assert project_dialog.project_name_error.text() == "Project name needs to be specified."
    assert project_dialog.project_name_error.isHidden()

    assert project_dialog.project_folder.placeholderText() == "Select project folder"
    assert project_dialog.project_folder_label.text() == "Project Folder:"
    assert project_dialog.project_folder_error.text() == "An empty project folder needs to be selected."
    assert project_dialog.project_folder_error.isHidden()
    assert project_dialog.project_folder.isReadOnly()

    assert not project_dialog.name_error
    assert not project_dialog.folder_error


def test_lineedit_errors(setup_project_dialog_widget):
    """
    Tests the project name and folder line edit errors displayed.
    """
    project_dialog, _ = setup_project_dialog_widget

    # tests the project name and folder line edit errors displayed.
    QtTest.QTest.mouseClick(project_dialog.create_button, QtCore.Qt.MouseButton.LeftButton)

    assert not project_dialog.project_name_error.isHidden()
    assert project_dialog.name_error
    assert not project_dialog.project_folder_error.isHidden()
    assert project_dialog.folder_error

    # tests the project name line edit error displayed.
    project_dialog.project_folder.setText("test-folder")
    QtTest.QTest.mouseClick(project_dialog.create_button, QtCore.Qt.MouseButton.LeftButton)

    assert not project_dialog.project_name_error.isHidden()
    assert project_dialog.name_error
    assert project_dialog.project_folder_error.isHidden()
    assert not project_dialog.folder_error

    # tests the project folder line edit error displayed.
    project_dialog.project_name.setText("test-name")
    project_dialog.project_folder.setText("")
    QtTest.QTest.mouseClick(project_dialog.create_button, QtCore.Qt.MouseButton.LeftButton)

    assert project_dialog.project_name_error.isHidden()
    assert not project_dialog.name_error
    assert not project_dialog.project_folder_error.isHidden()
    assert project_dialog.folder_error


@patch.object(MockParentWindow, "createNewProject")
def test_create_button(mock_create_new_project, setup_project_dialog_widget):
    """
    Tests create button on the ProjectDialog class.
    """
    project_dialog, _ = setup_project_dialog_widget

    project_dialog.project_name.setText("test-name")
    project_dialog.project_folder.setText("test-folder")
    QtTest.QTest.mouseClick(project_dialog.create_button, QtCore.Qt.MouseButton.LeftButton)
    mock_create_new_project.assert_called_once()


@patch.object(MockParentWindow, "toggleView")
def test_cancel_button(mock_toggle_view, setup_project_dialog_widget):
    """
    Tests cancel button on the ProjectDialog class.
    """
    project_dialog, _ = setup_project_dialog_widget

    project_dialog.project_name.setText("test-name")
    project_dialog.name_error = True
    project_dialog.project_folder.setText("test-folder")
    project_dialog.folder_error = True

    QtTest.QTest.mouseClick(project_dialog.cancel_button, QtCore.Qt.MouseButton.LeftButton)

    mock_toggle_view.assert_called_once()

    assert project_dialog.project_name.text() == ""
    assert not project_dialog.name_error
    assert project_dialog.project_folder.text() == ""
    assert not project_dialog.folder_error


@patch("os.listdir")
@patch("PyQt6.QtWidgets.QFileDialog.getExistingDirectory")
def test_browse_button(mock_get_existing_directory, mock_listdir, setup_project_dialog_widget):
    """
    Tests the browse button on the ProjectDialog class.
    """
    project_dialog, _ = setup_project_dialog_widget

    # When empty folder is selected.
    mock_get_existing_directory.return_value = "/test/folder/path"
    mock_listdir.return_value = [".hiddenfile"]

    QtTest.QTest.mouseClick(project_dialog.browse_button, QtCore.Qt.MouseButton.LeftButton)

    assert project_dialog.project_folder.text() == "/test/folder/path"
    assert not project_dialog.folder_error

    project_dialog.reset_variables()

    # When a non empty folder is selected.
    mock_listdir.return_value = [".hiddenfile", "testfile"]

    QtTest.QTest.mouseClick(project_dialog.browse_button, QtCore.Qt.MouseButton.LeftButton)

    assert project_dialog.project_folder.text() == ""
    assert project_dialog.folder_error
