import pytest

from rascal2.dialogs.about_dialog import AboutDialog
from rascal2.ui.view import MainWindowView


@pytest.fixture
def about():
    return AboutDialog()


def test_about_dialog_construction(about):
    assert about._rascal_label.text() == "information about RASCAL-2"


def test_update_info_works(about):
    """Check if update rascal info add all necessary information to the rascal label"""
    main_windows = MainWindowView()
    about.update_rascal_info(main_windows)
    rascal_info = about._rascal_label.text()
    assert "Version" in rascal_info
    assert "RasCAL 2" in rascal_info
    assert "Matlab Path:" in rascal_info
    assert "Log File:" in rascal_info
