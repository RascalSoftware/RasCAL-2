"""Widget for the Project window."""

from collections.abc import Generator
from copy import deepcopy

import ratapi
from pydantic import ValidationError
from PyQt6 import QtCore, QtGui, QtWidgets
from ratapi.utils.custom_errors import custom_pydantic_validation_error
from ratapi.utils.enums import Calculations, Geometries, LayerModels

from rascal2.widgets.project.lists import ContrastWidget, DataWidget
from rascal2.widgets.project.tables import (
    BackgroundsFieldWidget,
    CustomFileWidget,
    DomainContrastWidget,
    LayerFieldWidget,
    ParameterFieldWidget,
    ProjectFieldWidget,
    ResolutionsFieldWidget,
)

class SlidersViewWidget(QtWidgets.QWidget):
    """
    The sliders view Widget
    """

    def __init__(self, parent):
        """
        Initialize widget.

        Parameters
        ----------
        parent: MainWindowView
                An instance of the MainWindowView
        """
        super().__init__()
        self._parent = parent
        #self._parent_model = self.parent.presenter.model

        main_layout = QtWidgets.QVBoxLayout()
        #main_layout.setSpacing(20)

        self._accept_button = QtWidgets.QPushButton("Accept", self, objectName="Accept")
        self._accept_button.clicked.connect(self.save_changes)
        self._cancel_button = QtWidgets.QPushButton("Cancel", self, objectName="Cancel")
        self._cancel_button.clicked.connect(QtWidgets.QDialog.accept)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        button_layout.addWidget(self._accept_button)
        button_layout.addWidget(self._cancel_button)

        main_layout.addLayout(button_layout)


        #self.parent_model.project_updated.connect(self.update_project_view)
        #self.parent_model.controls_updated.connect(self.handle_controls_update)

        #project_view = self.create_project_view()

        #self.project_tab.currentChanged.connect(self.edit_project_tab.setCurrentIndex)
        #self.edit_project_tab.currentChanged.connect(self.project_tab.setCurrentIndex)


        self.setLayout(main_layout)

    def create_project_view(self) -> None:

        return

    def update_project_view(self, update_tab_index=None) -> None:
        """Updates the project view."""


    def handle_controls_update(self):
        """Handle updates to Controls that need to be reflected in the project."""

    def handle_model_update(self, new_entry):
        """Handle updates to the model type.

        Parameters
        ----------
        new_entry : LayerModels | Calculations
            The new layer model or calculation.

        """

    def show_project_view(self) -> None:
        """Show project view"""


    def save_changes(self) -> None:
        """Save changes to the project."""
        # sync list items (wrap around update_project_view() which sets them to zero by default)
        # the list can lose focus when a contrast is edited... default to first item if this happens
        errors = "\n  ".join(self.validate_draft_project())
        if errors:
            self.parent.terminal_widget.write_error(f"Could not save draft project:\n  {errors}")
        else:
            # catch errors from Pydantic as fallback rather than crashing
            try:
                self.parent.presenter.edit_project(self.draft_project)
            except ValidationError as err:
                custom_error_list = custom_pydantic_validation_error(err.errors(include_url=False))
                custom_errors = ValidationError.from_exception_data(err.title, custom_error_list, hide_input=True)
                self.parent.terminal_widget.write_error(f"Could not save draft project:\n  {custom_errors}")
            else:
                self.show_project_view()

