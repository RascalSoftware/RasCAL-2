"""Tests for the custom file editor."""

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PyQt6 import Qsci, QtWidgets
from ratapi.utils.enums import Languages

from rascal2.dialogs.custom_file_editor import (
    CustomFileEditorDialog,
    create_new_file,
    edit_file,
    edit_file_local,
    edit_file_matlab,
)
from tests.utils import assert_error_logged


@pytest.fixture
def custom_file_dialog():
    """Fixture for a custom file dialog."""
    parent = QtWidgets.QMainWindow()
    dlg = CustomFileEditorDialog(parent)
    dlg.show = MagicMock()
    yield dlg
    dlg.reject()


@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile("w+", suffix=".py", delete=False) as f:
        f.write("Test text for a test dialog!")
        f.flush()
        yield Path(f.name)
        f.close()


def test_edit_file_local(custom_file_dialog, mock_window_view):
    """Test that the dialog is executed when edit_file_local() is called on a valid file."""
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp, "testfile.py")
        file.touch()
        edit_file_local(file, Languages.Python, mock_window_view)

        custom_file_dialog.show.assert_called_once()


@pytest.mark.parametrize("filepath", ["dir/", "not_there.m"])
def test_edit_incorrect_file(filepath, caplog, mock_window_view):
    """A logger error should be emitted if a directory or nonexistent file is given to the editor."""
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp, filepath)
        edit_file_local(file, Languages.Python, mock_window_view)

    assert_error_logged(caplog, "Attempted to edit a custom file which does not exist!")


@patch("rascal2.dialogs.custom_file_editor.MatlabHelper", autospec=True)
def test_edit_file_matlab(mock_matlab):
    """Assert that a file is passed to the engine when the MATLAB editor is called."""
    mock_engine = MagicMock()
    mock_engine.edit = MagicMock()
    mock_helper = MagicMock()
    mock_helper.get_local_engine = MagicMock(return_value=mock_engine)
    mock_matlab.return_value = mock_helper
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp, "testfile.m")
        file.touch()
        edit_file_matlab(file)

    mock_helper.get_local_engine.assert_called_once()
    mock_engine.edit.assert_called_once_with(str(file))


@patch("rascal2.dialogs.custom_file_editor.MatlabHelper", autospec=True)
def test_edit_no_matlab_engine(mock_matlab, caplog):
    """A logging error should be produced if a user tries to edit a file in MATLAB with no engine available."""
    mock_helper = MagicMock()
    mock_helper.get_local_engine = MagicMock(side_effect=ValueError)
    mock_matlab.return_value = mock_helper
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp, "testfile.m")
        file.touch()
        edit_file_matlab(file)
    mock_helper.get_local_engine.assert_called_once()

    errors = [record for record in caplog.get_records("call") if record.levelno == logging.ERROR]
    assert len(errors) == 1
    assert "Attempted to edit a file in MATLAB engine" in caplog.text


@pytest.mark.parametrize(
    "language, expected_lexer",
    [(Languages.Python, Qsci.QsciLexerPython), (Languages.Matlab, Qsci.QsciLexerMatlab), (None, type(None))],
)
def test_dialog_init(custom_file_dialog, temp_file, language, expected_lexer):
    """Ensure the custom file editor is set up correctly."""
    custom_file_dialog.open_file(temp_file, language)

    assert isinstance(custom_file_dialog.editor.lexer(), expected_lexer)
    assert custom_file_dialog.editor.text() == "Test text for a test dialog!"


@patch("rascal2.dialogs.custom_file_editor.QtWidgets.QMessageBox")
def test_dialog_save(mock_msg_box, caplog, custom_file_dialog):
    """Text changes to the editor are saved to the file when save_file is called."""
    temp_file = MagicMock()
    temp_file.read_text = MagicMock(return_value="This is a test")

    custom_file_dialog.open_file(temp_file, Languages.Python)

    assert not custom_file_dialog.is_modified

    # No changes so no save
    custom_file_dialog.save_file()
    temp_file.write_text.assert_not_called()
    custom_file_dialog.unchanged_text = temp_file.read_text()

    custom_file_dialog.editor.setText("New test text...")

    assert custom_file_dialog.is_modified

    temp_file.is_relative_to = MagicMock(return_value=True)  # file is relative to example dir
    # No save in example dir
    custom_file_dialog.save_file()
    mock_msg_box.warning.assert_called_once()
    temp_file.write_text.assert_not_called()
    custom_file_dialog.unchanged_text = temp_file.read_text()

    temp_file.is_relative_to = MagicMock(return_value=False)
    custom_file_dialog.save_file()
    temp_file.write_text.assert_called_once()
    assert not custom_file_dialog.is_modified

    custom_file_dialog.editor.setText("User changed text")
    temp_file.write_text = MagicMock(side_effect=OSError)
    custom_file_dialog.save_file()
    assert_error_logged(caplog, f"Failed to save custom file to {custom_file_dialog.file}")
    mock_msg_box.critical.assert_called_once()


@patch("rascal2.dialogs.custom_file_editor.QtWidgets.QMessageBox.question")
def test_save_changes_when_opening_file(mock_msg_box, custom_file_dialog, temp_file):
    """Text changes to the editor are saved to the file when save_file is called."""
    custom_file_dialog.open_file(temp_file, Languages.Python)

    custom_file_dialog.editor.setText("New test text...")
    # Opening the same file should not trigger a save warning
    custom_file_dialog.open_file(temp_file, Languages.Python)

    mock_msg_box.assert_not_called()
    assert temp_file.read_text() != "New test text..."

    with tempfile.TemporaryDirectory() as tmp:
        new_file = Path(tmp, "filename.py")
        new_file.write_text("This is a new file")
        mock_msg_box.return_value = QtWidgets.QMessageBox.StandardButton.Save
        # Changing the file should save old file if user selects save in msg box
        custom_file_dialog.open_file(new_file, Languages.Python)
        mock_msg_box.assert_called_once()
        assert temp_file.read_text() == "New test text..."

        custom_file_dialog.editor.setText("Another test text...")
        mock_msg_box.return_value = QtWidgets.QMessageBox.StandardButton.Discard
        # Changes should be discarded as user selected discard in msg box
        custom_file_dialog.open_file(temp_file, Languages.Python)
        assert new_file.read_text() == "This is a new file"


@pytest.mark.parametrize(
    "language, file_type, domain",
    (
        ["python", "Background", False],
        ["python", "Model", True],
        ["python", "Model", False],
        ["matlab", "Background", False],
        ["matlab", "Model", True],
        ["matlab", "Model", False],
    ),
)
@patch("rascal2.dialogs.custom_file_editor.edit_file", autospec=True)
def test_create_file(mock_edit_file, mock_window_view, caplog, language, file_type, domain):
    with tempfile.TemporaryDirectory() as tmp:
        cur_dir = os.getcwd()
        try:
            os.chdir(tmp)
            create_new_file("hello world", language, domain, file_type, mock_window_view)
            mock_edit_file.assert_called()
            file = Path("hello_world.py" if language == "python" else "hello_world.m")
            assert file.is_file()
            assert file.read_text().find("hello_world(") != -1

            create_new_file("hello world", language, domain, file_type, mock_window_view)
            # non-unique name so file already exist
            assert_error_logged(
                caplog, f"The file ({file.name}) already exists, change custom file name to create a different file."
            )
        finally:
            os.chdir(cur_dir)


@pytest.mark.parametrize(
    "language, file_type, domain",
    (
        ["c++", "Background", False],
        ["c++", "Model", True],
    ),
)
@patch("rascal2.dialogs.custom_file_editor.edit_file", autospec=True)
def test_create_bad_file_type(mock_edit_file, mock_window_view, caplog, language, file_type, domain):
    create_new_file("hello world", language, domain, file_type, mock_window_view)
    mock_edit_file.assert_not_called()

    assert_error_logged(caplog, f"Creating a new file for {language} is not supported.")


@patch("rascal2.dialogs.custom_file_editor.SETTINGS", autospec=True)
@patch("rascal2.dialogs.custom_file_editor.edit_file_matlab", autospec=True)
@patch("rascal2.dialogs.custom_file_editor.edit_file_local", autospec=True)
def test_edit_file(mock_edit_file_local, mock_edit_file_matlab, mock_setting, mock_window_view):
    mock_setting.matlab_as_default_editor = False
    edit_file("hello", "python", mock_window_view)
    mock_edit_file_local.assert_called_once()

    mock_edit_file_matlab.return_value = True
    edit_file("hello", "matlab", mock_window_view)
    mock_edit_file_matlab.assert_called_once()
    assert mock_edit_file_local.call_count == 1

    mock_edit_file_matlab.return_value = False  # matlab editor failed so fallback on local
    mock_setting.matlab_as_default_editor = True
    edit_file("hello", "python", mock_window_view)
    assert mock_edit_file_matlab.call_count == 2
    assert mock_edit_file_local.call_count == 2
