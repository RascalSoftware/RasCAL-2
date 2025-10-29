"""Widget for the Project window."""

from collections.abc import Generator
from copy import deepcopy

import ratapi
from pydantic import ValidationError
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt
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
        self.mdi_holder = None # the variable contains reference to mdi container holding this window
        self._view_geometry = None # holder for slider view geometry, created to store slider view location
        # within the main window for subsequent calls to show sliders. Not yet restored from hdd properly
        # inherits project geometry on the first view.
        self._parent = parent

        self.create_sliders_layout()
        #self._parent_model = self.parent.presenter.model


        #self.parent_model.project_updated.connect(self.update_project_view)
        #self.parent_model.controls_updated.connect(self.handle_controls_update)

        #project_view = self.create_project_view()

        #self.project_tab.currentChanged.connect(self.edit_project_tab.setCurrentIndex)
        #self.edit_project_tab.currentChanged.connect(self.project_tab.setCurrentIndex)

    def show(self):
        """Overload parent show method to deal with mdi container"""
        if self.mdi_holder is None:
            self._view_geometry = None
            super().show()
        else:
            if self._view_geometry is None: # inherit geometry from project view
                for window in self._parent.mdi.subWindowList():
                    if window.windowTitle() == "Project":
                        self._view_geometry = window.geometry()
            self.mdi_holder.setGeometry(self._view_geometry)
            self.mdi_holder.show()

    def hide(self):
        """Overload parent hide method to deal with mdi container"""
        if self.mdi_holder is None:
            super().hide()
        else:
            # store sliders geometry which may be user changed for the following view
            self._view_geometry = self.mdi_holder.geometry()
            self.mdi_holder.hide()


    def create_sliders_layout(self) -> None:
        """ Create sliders layout with all necessary controls and connections """

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(20)

        accept_button = QtWidgets.QPushButton("Accept", self, objectName="AcceptButton")
        accept_button.clicked.connect(self.save_changes)
        cancel_button = QtWidgets.QPushButton("Cancel", self, objectName="CancelButton")
        cancel_button.clicked.connect(self.cancel_changes_from_sliders)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        button_layout.addWidget(accept_button)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        slider = LabeledSlider()
        main_layout.addWidget(slider)

        self.setLayout(main_layout)

    def init(self) -> None:
        """Initialize state, position and construction of the sliders widget
        i.e. set up everything except its show/hide state
         """


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

    def show_sliders_view(self) -> None:
        """Show project view"""
        self._parent.show_or_hide_sliders(True)

    def cancel_changes_from_sliders(self):
        """Cancel changes to properties obtained from sliders
        and hide sliders view.
        """
        self._parent.show_or_hide_sliders(False)

    def save_changes(self) -> None:
        """Save changes to the project."""
        # sync list items (wrap around update_project_view() which sets them to zero by default)
        # the list can lose focus when a contrast is edited... default to first item if this happens
        #errors = "\n  ".join(self.validate_draft_project())
        self._parent.show_or_hide_sliders(False)
        return
        errors = None
        if errors:
            self._parent.terminal_widget.write_error(f"Could not save draft project:\n  {errors}")
        else:
            # catch errors from Pydantic as fallback rather than crashing
            try:
                self._parent.presenter.edit_project(self.draft_project)
            except ValidationError as err:
                custom_error_list = custom_pydantic_validation_error(err.errors(include_url=False))
                custom_errors = ValidationError.from_exception_data(err.title, custom_error_list, hide_input=True)
                self._parent.terminal_widget.write_error(f"Could not save draft project:\n  {custom_errors}")
            else:
                self._parent.show_or_hide_sliders(False)


class LabeledSlider(QtWidgets.QWidget):
    def __init__(self, minimum=0, maximum=100, step=10, parent=None):
        super().__init__(parent)

        self.slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(minimum)
        self.slider.setMaximum(maximum)
        self.slider.setTickInterval(step)
        self.slider.setSingleStep(step)
        self.slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.slider.setValue((maximum + minimum) // 2)

        self.value_label = QtWidgets.QLabel(str(self.slider.value()), alignment=Qt.AlignmentFlag.AlignCenter)

        # layout for numeric scale below
        self.scale_layout = QtWidgets.QHBoxLayout()
        for i in range(minimum, maximum + 1, step):
            label = QtWidgets.QLabel(str(i))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scale_layout.addWidget(label)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.slider)
        layout.addLayout(self.scale_layout)
        layout.addWidget(self.value_label)

        # signal to update label dynamically
        self.slider.valueChanged.connect(self._update_value)

    def _update_value(self, val):
        self.value_label.setText(f"Value: {val}")
