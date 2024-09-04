import warnings
from concurrent.futures import ProcessPoolExecutor
from contextlib import redirect_stdout
from typing import Any

import RATapi as RAT
from tqdm.auto import tqdm

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
        if hasattr(self, "pool"):
            self.process.cancel()

    def run(self):
        """Run RAT."""
        self.pool = ProcessPoolExecutor()
        rat_inputs = RAT.inputs.make_input(self.model.project, self.model.controls)
        self.model.controls.procedure = "dream"
        display_on = self.model.controls.display != RAT.utils.enums.Display.Off

        with redirect_stdout(self.view.terminal_widget), StdoutHandler(self.view.terminal_widget, display_on):
            self.process = self.pool.submit(run_rat, rat_inputs, self.model.controls.procedure)

            results = self.process.result()
            print(results)
        self.view.handle_run_finish()


def run_rat(rat_inputs: tuple, procedure: str) -> RAT.outputs.Results | RAT.outputs.BayesResults:
    """Run RAT and retrieve the results object.

    Parameters
    ----------
    rat_inputs : tuple
        The C++ inputs for RAT.
    procedure : str
        The method procedure.

    Returns
    -------
    RAT.outputs.Results | RAT.outputs.BayesResults
        The results of the RAT calculation.

    """
    problem_definition, cells, limits, priors, cpp_controls = rat_inputs
    problem_definition, output_results, bayes_results = RAT.rat_core.RATMain(
        problem_definition, cells, limits, cpp_controls, priors
    )
    results = RAT.outputs.make_results(procedure, output_results, bayes_results)

    return results


class StdoutHandler:
    """Context manager to handle stdout and direct it to a terminal widget."""

    def __init__(self, terminal, display: bool):
        self.terminal = terminal
        self.display = display
        self.pbar = None
        self.tqdm_kwargs = {
            "total": 100,
            "desc": "",
            "bar_format": "{l_bar}{bar}",
            "disable": not self.display,
            "file": self.terminal,
        }

    def __enter__(self):
        if self.display:
            RAT.events.register(RAT.events.EventTypes.Message, self.terminal.write)
            RAT.events.register(RAT.events.EventTypes.Progress, self.print_progress)

    def print_progress(self, event):
        if self.pbar is None:
            self.pbar = tqdm(**self.tqdm_kwargs)
        value = event.percent * 100
        self.pbar.desc = event.message
        self.pbar.update(value - self.pbar.n)

    def __exit__(self, _exc_type, _exc_val, _traceback):
        if self.pbar is not None:
            self.pbar.close()
            print("")  # Print new line after bar
            RAT.events.clear(RAT.events.EventTypes.Message, self.terminal.write)
            RAT.events.clear(RAT.events.EventTypes.Message, self.print_progress)
