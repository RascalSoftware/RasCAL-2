import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ["DELAY_MATLAB_START"] = "1"
import pytest
from PyQt6 import QtCore, QtWidgets

APP = QtWidgets.QApplication([])
GLOBAL_SETTING = None


@pytest.fixture
def qt_application():
    return APP


@pytest.fixture
def global_setting():
    return GLOBAL_SETTING


@pytest.fixture
def mock_window_view():
    return MockWindowView()


@pytest.fixture(scope="session", autouse=True)
def mock_setting(request):
    global GLOBAL_SETTING
    tmp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    ini_file = Path(tmp_dir.name) / "settings.ini"
    GLOBAL_SETTING = QtCore.QSettings(str(ini_file), QtCore.QSettings.Format.IniFormat)
    setting_patch = []
    for target in ["rascal2.ui.view.get_global_settings", "rascal2.settings.get_global_settings"]:
        setting_patch.append(patch(target, return_value=GLOBAL_SETTING))
        setting_patch[-1].start()

    def teardown_mock_setting():
        global GLOBAL_SETTING
        GLOBAL_SETTING = None
        tmp_dir.cleanup()
        for target in setting_patch:
            target.stop()

    request.addfinalizer(teardown_mock_setting)


class MockUndoStack:
    """A mock Undo stack."""

    def __init__(self):
        self.stack = []
        self.clean = True

    def push(self, command):
        self.clean = False
        command.redo()

    def setClean(self):
        self.clean = True

    def isClean(self):
        return self.clean


class MockWindowView(QtWidgets.QMainWindow):
    """A mock MainWindowView class."""

    def __init__(self):
        super().__init__()
        self.undo_stack = MockUndoStack()
        self.presenter = MagicMock()
        self.controls_widget = MagicMock()
        self.project_widget = MagicMock()
        self.terminal_widget = MagicMock()
        self.plot_widget = MagicMock()
        self.handle_results = MagicMock()
        self.settings = MagicMock()
        self.get_project_folder = lambda: "new path/"
        self.windowTitle = lambda: "RasCAL2"
        self.show_message = MagicMock()
        self.toggle_sliders = MagicMock()
        self.set_editing_enabled = MagicMock()
