"""Widget for the Sliders View window."""

from copy import deepcopy

import ratapi
import ratapi.models
from PyQt6 import QtCore,QtWidgets


class SlidersViewWidget(QtWidgets.QWidget):
    """
    The sliders view Widget represents properties user intends to fit.
    The sliders allow user to change the properties and immediately see how the change affects contrast.
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
        self.mdi_holder = None   # the variable contains reference to mdi container holding this widget
        self._view_geometry = None  # holder for slider view geometry, created to store slider view location
        # within the main window for subsequent calls to show sliders. Not yet restored from hdd properly
        # inherits project geometry on the first view.
        self._parent = parent  # reference to main view widget which holds sliders view

        self._prop_to_revert ={}  # dictionary of original properties with fit parameter "true" but have to be restored
        # back into original project if cancel button is pressed
        self._prop_to_change = {}  # dictionary of references to properties with fit parameter "true" to build sliders
        # for and allow changes when slider is moved. Their values are reflected in project and affect plots

        self._sliders = {}   # dictionary of the sliders used to display fittable values
        # create initial slider view layout and everything else which depends on it
        self.init()


    def show(self):
        """Overload parent show method to deal with mdi container
           showing sliders widget window. Also sets up or updates sliders
           widget list depending on previous state of the widget
        """

        self.init()
        if self.mdi_holder is None:
            self._view_geometry = None
            super().show()
        else:
            if self._view_geometry is None:
                # inherit geometry from project view
                for window in self._parent.mdi.subWindowList():
                    if window.windowTitle() == "Project":
                        self._view_geometry = window.geometry()

            self.mdi_holder.setGeometry(self._view_geometry)
            self.mdi_holder.show()

    def hide(self):
        """Overload parent hide method to deal with mdi container
           hiding slider widgets window
        """
        if self.mdi_holder is None:
            super().hide()
        else:
            # store sliders geometry which may be user changed for the following view
            self._view_geometry = self.mdi_holder.geometry()
            self.mdi_holder.hide()

    def init(self) -> None:
        """The main Widget window is ready so this method initializes
           general contents (buttons) of the sliders widget.
           If project is defined it extracts properties, used to build
           sliders and generates list of sliders widgets to
           control the properties.
         """
        if self.findChild(QtWidgets.QWidget,'AcceptButton') is None:
            self._create_slider_view_layout()

        proj = self._parent.presenter.model.project
        update_sliders = self._init_properties_for_sliders(proj)
        if update_sliders:
            self._update_sliders_widgets()
        else:
            self._add_sliders_widgets()

    def _init_properties_for_sliders(self,project : ratapi.Project) -> bool:
        """Take project and copy all properties which have attribute "Fit" == True
           into dictionary used to build sliders for them. Also set back-up properties
           dictionary used to reset properties back to their default values if "Cancel"
           button is pressed.

           Input:
           ------
           project: ratapi.Project  -- project to get properties to change

           Returns:
           --------
           update_properties -- true if all properties in the project have already
           had sliders, generated for them so we may update existing widgets instead of generating
           new ones.
         """
        if project is None:
            return False

        trial_properties = {}
        n_existing_properties = 0
        for field_name in ratapi.Project.model_fields:
            attr = getattr(project, field_name)
            if isinstance(attr, ratapi.ClassList):
                param_list = attr.data
                for prop in param_list:
                    if isinstance(prop,ratapi.models.Parameter) and prop.fit:
                        trial_properties[prop.name] = prop
                        if prop.name in self._prop_to_change:
                            n_existing_properties += 1

        update_properties = n_existing_properties == len(trial_properties) # if all properties of trial dictionary
        # are in existing dictionary, we will update widgets instead of adding the new one
        self._prop_to_change = trial_properties               # References to project properties
        self._prop_to_revert = deepcopy(self._prop_to_change) # Copy of initial values of project properties
        return update_properties

    def _create_slider_view_layout(self) -> None:
        """ Create sliders layout with all necessary controls and connections
            but without sliders themselves.
        """

        main_layout = QtWidgets.QVBoxLayout()
        #main_layout.setSpacing(20)

        accept_button = QtWidgets.QPushButton("Accept", self, objectName="AcceptButton")
        accept_button.clicked.connect(self._apply_changes_from_sliders)
        cancel_button = QtWidgets.QPushButton("Cancel", self, objectName="CancelButton")
        cancel_button.clicked.connect(self._cancel_changes_from_sliders)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        button_layout.addWidget(accept_button)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _add_sliders_widgets(self) -> None:
        """ Given sliders view layout and list of properties which can be controlled by sliders
            add appropriate sliders to sliders view Widget
        """
        scroll = self.findChild(QtWidgets.QScrollArea, "Scroll")
        if scroll is None:
            main_layout = self.layout()
            scroll = QtWidgets.QScrollArea()
            scroll.setWidgetResizable(True)  # important: resize content to fit area
            scroll.setObjectName("Scroll")
            main_layout.addWidget(scroll)
            content = QtWidgets.QWidget()
            content.setObjectName("Scroll_content")
            scroll.setWidget(content)
            # --- Add content layout
            content_layout = QtWidgets.QVBoxLayout(content)
        else:
            content = scroll.findChild(QtWidgets.QWidget, "Scroll_content")
            content_layout = content.layout()

        # We are adding new sliders, so delete all previous ones
        for slider in self._sliders.values():
            slider.deleteLater()
        self._sliders = {}

        if len(self._prop_to_change) == 0:
            no_label = QtWidgets.QLabel("No properties to fit, Nothing to view here")
            no_label.setObjectName("No_properties_to_fit")
            content_layout.addWidget(no_label)
            self._sliders['No_properties_to_fit_label'] = no_label
        else:
            content_layout.setSpacing(0)
            for prop in self._prop_to_change.values():
                slider = LabeledSlider(prop)

                self._sliders[prop.name] = slider
                content_layout.addWidget(slider)

    def _update_sliders_widgets(self) -> None:
        """Updates the sliders given the project properties to fit are the same
           but their values may be upgraded
        """
        for name,slider in self._sliders.items():
            self._sliders[name].update_slider_parameters(self._prop_to_change[name])

    def show_sliders_view(self) -> None:
        """Show project view"""
        self._parent.show_or_hide_sliders(True)

    def _cancel_changes_from_sliders(self):
        """Cancel changes to properties obtained from sliders
        and hide sliders view.
        """
        # as here our properties to change refer directly to project properties
        # we modify their values directly
        for key,prop in self._prop_to_revert.items():
            self._prop_to_change[key].value = prop.value

        self._parent.show_or_hide_sliders(False)

    def _apply_changes_from_sliders(self) -> None:
        """Apply changes obtained from sliders to the project
           and make them permanent
        """
        for key,prop in self._prop_to_change.items():
            self._prop_to_revert[key].value = prop.value

        # TODO: Re #149 update project view:
        self._parent.show_or_hide_sliders(False)
        return
#=======================================================================================================================
class LabeledSlider(QtWidgets.QFrame):
    def __init__(self, param: ratapi.models.Parameter, parent=None):
        super().__init__(parent)
        self._prop = param  # hold the property controlled by slider
        self.slider_name = param.name # name the slider as the property it refers to

        # Defaults for property min/max. Will be overwritten
        self._value_min = 0       # default minimal value property may have
        self._value_range = 100   # default maximal value the property may have
        self._value_step = 1      # the change in property value per single step slider move

        # Properties of slider widget:
        self._num_slider_ticks = 11
        self._slider_max_idx = 100  # defines accuracy of slider motion
        self._ticks_step = 10       # sliders ticks
        self._labels = []           # number of slider labels can not change too
        self._value_label_format = "{:.3g}"  # format to display slider value
        self._tick_label_format = "{:.2g}"  # format to display numbers under the sliders ticks

        self.update_slider_parameters(param,True)

        # Build all sliders widget and arrange them as expected
        self._slider = self._build_slider(param.value)

        # name of given slider can not change. It will be different slider with different name
        name_label = QtWidgets.QLabel(self.slider_name, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self._value_label = QtWidgets.QLabel(self._value_label_format.format(param.value), alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        lab_layout = QtWidgets.QHBoxLayout()
        lab_layout.addWidget(name_label)
        lab_layout.addWidget(self._value_label)

        # layout for numeric scale below
        scale_layout = QtWidgets.QHBoxLayout()

        tick_step = self._value_range / self._num_slider_ticks
        for idx in range(0,self._num_slider_ticks + 1):
            tick_value = self._value_min+idx*tick_step
            label = QtWidgets.QLabel(self._tick_label_format.format(tick_value))
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
            scale_layout.addWidget(label)
            self._labels.append(label)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(lab_layout)
        layout.addWidget(self._slider)
        layout.addLayout(scale_layout)

        # signal to update label dynamically
        self._slider.valueChanged.connect(self._update_value)

        self.setObjectName(self.slider_name)
        self.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)


    def update_slider_parameters(self, param: ratapi.models.Parameter, in_constructor = False):
        """Modifies slider values which may change for this slider from his parent property"""

        # Characteristics of the property value to display
        self._value_min = self._prop.min
        self._value_range = (self._prop.max - self._value_min)
        # the change in property value per single step slider move
        self._value_step = self._value_range / self._slider_max_idx

        if in_constructor:
            return
        # otherwise, update slider's labels
        self._value_label.setText(self._value_label_format.format(param.value))
        tick_step = self._value_range / self._num_slider_ticks
        for idx in range(0,self._num_slider_ticks+1):
            tick_value = self._value_min+idx*tick_step
            self._labels[idx].setText(self._tick_label_format.format(tick_value))


    def _value_to_slider_pos(self, value: float) -> int:
        """Convert double property value into slider position"""
        return int(round(self._slider_max_idx*(value-self._value_min)/self._value_range,0))

    def _slider_pos_to_value(self,index: int) -> float:
        """convert double property value into slider position"""
        return self._value_min + index*self._value_step


    def _build_slider(self,initial_value: float) -> QtWidgets.QSlider:
        """Construct slider widget with integer scales and ticks in integer positions """

        slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(self._slider_max_idx)
        slider.setTickInterval(self._ticks_step)
        slider.setSingleStep(self._slider_max_idx)
        slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBothSides)
        slider.setValue(self._value_to_slider_pos(initial_value))

        return slider

    def _update_value(self, idx: int)->None:
        val = self._slider_pos_to_value(idx)
        self._value_label.setText(self._value_label_format.format(val))
        self._prop.value = val
