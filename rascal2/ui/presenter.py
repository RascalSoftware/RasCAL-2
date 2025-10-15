import re
import warnings
from pathlib import Path
from typing import Any

import ratapi as rat
import ratapi.wrappers

from rascal2.config import EXAMPLES_PATH, MATLAB_HELPER, get_matlab_engine
from rascal2.core import commands
from rascal2.core.enums import UnsavedReply
from rascal2.core.runner import LogData, RATRunner
from rascal2.settings import update_recent_projects

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
        self.worker = None

    def create_project(self, name: str, save_path: str):
        """Creates a new RAT project and controls object then initialise UI.

        Parameters
        ----------
        name : str
            The name of the project.
        save_path : str
            The save path of the project.

        """
        self.model.create_project(name, save_path)
        self.initialise_ui()

    def load_project(self, load_path: str):
        """Load an existing RAT project then initialise UI.

        Parameters
        ----------
        load_path : str
            The path from which to load the project.

        """
        self.model.load_project(load_path)
        if self.model.results is None:
            self.model.results = self.quick_run()
        update_recent_projects(load_path)

    def load_r1_project(self, load_path: str):
        """Load a RAT project from a RasCAL-1 project file.

        Parameters
        ----------
        load_path : str
            The path to the R1 file.

        """
        self.model.load_r1_project(load_path)
        self.model.results = self.quick_run(self.model.project)

    def initialise_ui(self):
        """Initialise UI for a project."""
        self.view.setWindowTitle(
            self.title + " - " + self.model.project.name,
        )
        self.view.init_settings_and_log(self.model.save_path)
        self.view.setup_mdi()
        self.view.plot_widget.update_plots()
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
            self.view.undo_stack.push(commands.EditControls({setting: value}, self))

    def save_project(self, save_as: bool = False):
        """Save the model.

        Parameters
        ----------
        save_as : bool
            Whether we are saving to the existing save path or to a specified folder.

        Returns
        -------
         : bool
            Indicates if the project was saved.
        """
        # we use this isinstance rather than `is not None`
        # because some PyQt signals will send bools and so on to this as a slot!
        if save_as or Path(self.model.save_path).is_relative_to(EXAMPLES_PATH):
            to_path = self.view.get_project_folder()
            if not to_path:
                return False
            self.model.save_path = to_path

        self.model.save_project()
        update_recent_projects(self.model.save_path)
        self.view.undo_stack.setClean()
        return True

    def ask_to_save_project(self):
        """Warn the user of unsaved changes."""
        proceed = True

        if not self.view.undo_stack.isClean():
            message = f'The project has been modified.\n\nDo you want to save changes to "{self.model.project.name}"?'
            reply = self.view.show_unsaved_dialog(message)
            if reply == UnsavedReply.Save:
                proceed = self.save_project()
            elif reply == UnsavedReply.Cancel:
                proceed = False

        return proceed

    def export_results(self):
        """Export the results object."""
        if self.model.results:
            filename = self.model.project.name.replace(" ", "_")
            save_file = self.view.get_save_file("Export Results", filename, "*.json")
            if not save_file:
                return

            try:
                self.model.results.save(save_file)
            except OSError as err:
                self.view.logging.error(f"Failed to save project at path {save_file}.\n", exc_info=err)

    def interrupt_terminal(self):
        """Sends an interrupt signal to the RAT runner."""
        self.runner.interrupt()

    def quick_run(self):
        """Run rat calculation with calculate procedure.

        Returns
        -------
        results : Union[ratapi.outputs.Results, ratapi.outputs.BayesResults]
            The calculation results.
        """
        if ratapi.wrappers.MatlabWrapper.loader is None and any(
            [file.language == "matlab" for file in self.model.project.custom_files]
        ):
            result = get_matlab_engine(MATLAB_HELPER.ready_event, MATLAB_HELPER.engine_output)
            if isinstance(result, Exception):
                raise result
        return rat.run(self.model.project, rat.Controls(display="off"))[1]

    def run(self):
        """Run rat using multiprocessing."""
        # reset terminal
        self.view.terminal_widget.progress_bar.setVisible(False)
        if self.view.settings.clear_terminal:
            self.view.terminal_widget.clear()

        # hide bayes plots button so users can't open plots during run
        self.view.plot_widget.bayes_plots_button.setVisible(False)

        rat_inputs = rat.inputs.make_input(self.model.project, self.model.controls)
        display_on = self.model.controls.display != rat.utils.enums.Display.Off

        self.runner = RATRunner(rat_inputs, self.model.controls.procedure, display_on)
        self.runner.finished.connect(self.handle_results)
        self.runner.stopped.connect(self.handle_interrupt)
        self.runner.event_received.connect(self.handle_event)
        self.runner.start()

    def handle_results(self):
        """Handle a RAT run being finished."""
        self.view.undo_stack.push(
            commands.SaveCalculationOutputs(
                self.runner.updated_problem,
                self.runner.results,
                self.view.terminal_widget.text_area.toPlainText(),
                self,
            )
        )
        self.view.handle_results(self.runner.results)

    def handle_interrupt(self):
        """Handle a RAT run being interrupted."""
        if self.runner.error is None:
            self.view.logging.info("RAT run interrupted!")
        else:
            self.view.logging.error("RAT run failed with exception.\n", exc_info=self.runner.error)
        self.view.reset_widgets()

    def handle_event(self):
        """Handle event data produced by the RAT run."""
        event = self.runner.events.pop(0)
        match event:
            case str():
                self.view.terminal_widget.write(event)
                chi_squared = get_live_chi_squared(event, str(self.model.controls.procedure))
                if chi_squared is not None:
                    self.view.controls_widget.chi_squared.setText(chi_squared)
            case rat.events.ProgressEventData():
                self.view.terminal_widget.update_progress(event)
            case rat.events.PlotEventData():
                self.view.plot_widget.plot_with_blit(event)
            case LogData():
                self.view.logging.log(event.level, event.msg)

    def edit_project(self, updated_project: dict, preview: bool = False) -> None:
        """Edit the Project with a dictionary of attributes.

        Parameters
        ----------
        updated_project : dict
            The updated project attributes.
        preview : bool
            indicates if the result should be previewed after update.

        Raises
        ------
        ValidationError
            If the updated project attributes are not valid.

        """
        project_dict = self.model.project.model_dump()
        project_dict.update(updated_project)
        self.model.project.model_validate(project_dict)
        self.view.undo_stack.push(commands.EditProject(updated_project, self, preview=preview))


# '\d+\.\d+' is the regex for
# 'some integer, then a decimal point, then another integer'
# the parentheses () mean it is put in capture group 1,
# which is what we return as the chi-squared value
# we compile these regexes on import to make `get_live_chi_squared` basically instant
chi_squared_patterns = {
    "simplex": re.compile(r"(\d+\.\d+)"),
    "de": re.compile(r"Best: (\d+\.\d+)"),
}


def get_live_chi_squared(item: str, procedure: str) -> str | None:
    """Get the chi-squared value from iteration message data.

    Parameters
    ----------
    item : str
        The iteration message.
    procedure : str
        The procedure currently running.

    Returns
    -------
    str or None
        The chi-squared value from that procedure's message data in string form,
        or None if one has not been found.

    """
    if procedure not in chi_squared_patterns:
        return None
    # match returns None if no match found, so whether one is found can be checked via 'if match'
    return match.group(1) if (match := chi_squared_patterns[procedure].search(item)) else None
