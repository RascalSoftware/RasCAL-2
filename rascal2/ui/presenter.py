import warnings
from typing import Any

from pydantic import ValidationError

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
        self.undo_stack = self.view.undo_stack

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

    def getControlsAttribute(self, setting) -> Any:
        """Get the value of an attribute in the model's Controls object.
        
        Parameters
        ----------
        setting : str
            Which setting in the Controls object should be read. 
        
        Returns
        -------
        value : Any
            The value of the setting in the model's Controls object.
        """
        value = getattr(self.model.controls, setting)
        return value

    def editControls(self, setting: str, value: Any) -> bool:
        """Edit a setting in the Controls object.

        Parameters
        ----------
        setting : str
            Which setting in the Controls object should be changed.
        value : Any
            The value which the setting should be changed to.

        Returns
        -------
        bool
            Whether the edit was successful.
        """
        # FIXME: without proper logging,
        # we have to check validation in advance because PyQt doesn't return
        # the exception, it just falls over in C++
        # also doing it this way stops bad changes being pushed onto the stack
        # also suppress warnings (we get warning for setting params not matching
        # procedure on initialisation) to avoid clogging stdout
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                self.model.controls.model_validate({setting: value})
            except ValidationError as err:
                self.last_validation_error = err
                return False
            self.view.undo_stack.push(commands.editControls(self.model.controls, setting, value))
            return True

    def interrupt_terminal(self):
        """Sends an interrupt signal to the terminal."""
        # TODO: stub for when issue #9 is resolved
        pass
