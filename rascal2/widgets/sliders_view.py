"""Widget for the Sliders View window."""

from collections.abc import Generator
from copy import deepcopy

import ratapi
import ratapi.models
from pydantic import ValidationError
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt
from ratapi.utils.custom_errors import custom_pydantic_validation_error
from ratapi.utils.enums import Calculations, Geometries, LayerModels


from rascal2.widgets.project.project import create_draft_project

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

        self._create_slider_view_layout()
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
            main_layout = self.layout()
            self._create_sliders_view(main_layout)
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


    def _create_slider_view_layout(self) -> None:
        """ Create sliders layout with all necessary controls and connections """

        main_layout = QtWidgets.QVBoxLayout()
        #main_layout.setSpacing(20)

        accept_button = QtWidgets.QPushButton("Accept", self, objectName="AcceptButton")
        accept_button.clicked.connect(self.save_changes)
        cancel_button = QtWidgets.QPushButton("Cancel", self, objectName="CancelButton")
        cancel_button.clicked.connect(self.cancel_changes_from_sliders)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        button_layout.addWidget(accept_button)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def init(self) -> None:
        """Initialize state, position and construction of the sliders widget
        i.e. set up everything except its show/hide state
         """


    def _create_sliders_view(self,main_layout) -> None:

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)  # important: resize content to fit area
        main_layout.addWidget(scroll)
        content = QtWidgets.QWidget()
        scroll.setWidget(content)
        # --- Add content layout
        content_layout = QtWidgets.QVBoxLayout(content)

        project = self._parent.presenter.model.project
        prop_dictionary = create_draft_project(project)
        for obj in prop_dictionary.values():
            if isinstance(obj, ratapi.ClassList):
                for prop in obj:
                    if hasattr(prop,"fit") and prop.fit:
                        slider = LabeledSlider(prop)
                        content_layout.addWidget(slider)


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

#=======================================================================================================================
class LabeledSlider(QtWidgets.QWidget):
    def __init__(self, param: ratapi.models.Parameter, parent=None):
        super().__init__(parent)
        self._prop = param  # hold the property controlled by slider

        # Properties of slider widget:
        self._slider_min_idx = 0
        self._slider_max_idx = 100 # defines accuracy of slider motion
        self._ticks_step = 10      # sliders ticks

        # Characteristics of the property value to display
        self._value_min   = self._prop.min
        self._value_range = (self._prop.max-self._value_min)
        # the change in property value per single step slider move
        self._value_step = self._value_range/self._slider_max_idx

        # Build all sliders widget and arrange them as expected
        self._slider = self._build_slider(param.value)

        name_label = QtWidgets.QLabel(param.name, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self._value_label = QtWidgets.QLabel(str(f"{param.value:.3g}"), alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        lab_layout = QtWidgets.QHBoxLayout()
        lab_layout.addWidget(name_label)
        lab_layout.addWidget(self._value_label)

        # layout for numeric scale below
        scale_layout = QtWidgets.QHBoxLayout()
        for idx in range(self._slider_min_idx, self._slider_max_idx, self._ticks_step):
            tick_value = self._slider_pos_to_value(idx)
            label = QtWidgets.QLabel(str(f"{tick_value:.2g}"))
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            scale_layout.addWidget(label)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(lab_layout)
        layout.addWidget(self._slider)
        layout.addLayout(scale_layout)

        # signal to update label dynamically
        self._slider.valueChanged.connect(self._update_value)

    def _value_to_slider_pos(self, value: float) -> int:
        """Convert double property value into slider position"""
        return int(round(self._slider_max_idx*(value-self._value_min)/self._value_range,0))

    def _slider_pos_to_value(self,index: int) -> float:
        """convert double property value into slider position"""
        return self._value_min + index*self._value_step

    def _build_slider(self,initial_value: float) -> QtWidgets.QSlider:
        """Construct slider widget with integer scales"""

        slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        slider.setMinimum(self._slider_min_idx)
        slider.setMaximum(self._slider_max_idx)
        slider.setTickInterval(self._ticks_step)
        slider.setSingleStep(self._slider_max_idx)
        slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBothSides)
        slider.setValue(self._value_to_slider_pos(initial_value))

        return slider

    def _update_value(self, idx: int)->None:
        val = self._slider_pos_to_value(idx)
        self._value_label.setText(str(f"{val:.3g}"))
        self._prop.value = val
