import warnings
from contextlib import redirect_stdout
from typing import Any
from contextlib import redirect_stderr, redirect_stdout

import RATapi as RAT
from PyQt6 import QtCore

from rascal2.core import commands

from .model import MainWindowModel


class MainWindowPresenter:
    """Facilitates interaction between View and Model

    Parameters
    ----------
    view : MainWindow
        main window view instance.
    """

    def __init__(self, view):
        self.view = view
        self.model = MainWindowModel()
        self.title = self.view.windowTitle()

    def create_project(self, name: str, save_path: str):
        """Creates a new RAT project and controls object then initialise UI.

        Parameters
        ----------
        name : str
            The name of the project.
        save_path : str
            The save path of the project.

        """

        self.view.setWindowTitle(self.title + " - " + name)
        self.model.create_project(name, save_path)
        # TODO if the view's central widget is the startup one then setup MDI else reset the widgets.
        # https://github.com/RascalSoftware/RasCAL-2/issues/15
        self.view.init_settings_and_log(save_path)
        self.view.setup_mdi()
        self.view.undo_stack.clear()
        self.view.enable_elements()

    def edit_controls(self, setting: str, value: Any):
        """Edit a setting in the Controls object.

        Parameters
        ----------
        setting : str
            Which setting in the Controls object should be changed.
        value : Any
            The value which the setting should be changed to.

        Raises
        ------
        ValidationError
            If the setting is changed to an invalid value.

        """
        # FIXME: without proper logging,
        # we have to check validation in advance because PyQt doesn't return
        # the exception, it just falls over in C++
        # also doing it this way stops bad changes being pushed onto the stack
        # https://github.com/RascalSoftware/RasCAL-2/issues/26
        # also suppress warnings (we get warning for setting params not matching
        # procedure on initialisation) to avoid clogging stdout
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model.controls.model_validate({setting: value})
            self.view.undo_stack.push(commands.EditControls(self.model.controls, setting, value))
            return True

    def interrupt_terminal(self):
        """Sends an interrupt signal to the terminal."""
        # TODO: stub for when issue #9 is resolved
        # https://github.com/RascalSoftware/RasCAL-2/issues/9
        pass

    def run(self):
        """Run RAT."""
        self.run_thread = QtCore.QThread(self.view)
        self.runner = RATRunner(self.model.project, self.model.controls)
        self.runner.moveToThread(self.run_thread)
        self.runner.finished.connect(self.run_thread.quit)
        self.runner.stdout.text_sent.connect(self.view.terminal_widget.write)
        self.run_thread.started.connect(self.runner.run)
        self.run_thread.start()


class RATRunner(QtCore.QObject):
    """Class to run RAT in a QThread."""

    finished = QtCore.pyqtSignal()

    def __init__(self, project, controls):
        super().__init__()

        self.project = project
        self.controls = controls
        # if we use self.view.terminal_widget as the io stream, then
        # we get a segfault for trying to use it between threads. so
        # we use a pyqt signal to send messages between threads
        self.stdout = StdoutEmitter()

    def run(self):
        """Run RAT with the given project and controls."""
        # for testing as we currently do not have project and control creation
        with redirect_stdout(self.stdout), redirect_stderr(self.stdout):
            project, results = RAT.run(self.project, self.controls)
        self.finished.emit()


class StdoutEmitter(QtCore.QObject):
    """Thread-safe stream to send signals for text."""

    text_sent = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def write(self, text):
        self.text_sent.emit(text)

    def flush(self):
        pass
