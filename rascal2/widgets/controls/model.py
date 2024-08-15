import warnings

from pydantic_core import ValidationError
from RATapi.controls import fields

from rascal2.core.commands import editControls


class FitSettingsModel:
    """TableModel to interface Controls fit settings with the view."""

    def __init__(self, presenter):
        super().__init__()
        self.presenter = presenter
        self.controls = self.presenter.model.controls
        self.model_fields = self.controls.model_fields
        self.undo_stack = self.presenter.undo_stack
        self.editable = True
        self.last_validation_error = ""

    def data(self, setting):
        value = getattr(self.controls, setting)
        return str(value)

    def setData(self, setting, value) -> bool:
        # we have to check validation in advance because PyQt doesn't return
        # the exception, it just falls over in C++
        # also doing it this way stops bad changes being pushed onto the stack
        try:
            with warnings.catch_warnings():  # warning is erroneous...
                warnings.simplefilter("ignore")
                self.controls.model_validate({setting: value})
        except ValidationError as err:
            self.last_validation_error = err
            return False
        self.undo_stack.push(editControls(self.controls, setting, value))
        print(self.controls)
        return True

    def get_procedure_settings(self, procedure):
        return [f for f in fields.get(procedure, []) if procedure != "procedure"]
