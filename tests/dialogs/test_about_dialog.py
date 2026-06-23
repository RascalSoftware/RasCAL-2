from unittest.mock import MagicMock, patch

from PyQt6 import QtWidgets

from rascal2.dialogs.about_dialog import AboutDialog


@patch("rascal2.dialogs.about_dialog.MatlabHelper", autospec=True)
def test_update_info_works(mock_matlab):
    """Check if `update_rascal_info` adds all necessary information to the dialog."""
    helper = MagicMock()
    mock_matlab.return_value = helper
    helper.get_matlab_path.return_value = "Test_Path"
    parent = QtWidgets.QMainWindow()
    about = AboutDialog(parent)
    assert about._rascal_label.text() == "information about RASCAL-2"

    about.update_rascal_info()
    rascal_info = about._rascal_label.text()
    assert "Version" in rascal_info
    assert "RasCAL 2" in rascal_info
    assert "Matlab Path:</td><td>Test_Path" in rascal_info
    assert "Log File:" in rascal_info

    helper.get_matlab_path.return_value = ""
    about.update_rascal_info()
    assert "Matlab Path:</td><td>None" in about._rascal_label.text()
