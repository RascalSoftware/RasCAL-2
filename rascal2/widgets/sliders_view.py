"""Widget for the Sliders View window."""

from copy import deepcopy

import ratapi.models
from PyQt6 import QtCore,QtWidgets

from rascal2.widgets.project.tables import (
    ParametersModel
)


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
        self.mdi_holder = None  # the variable contains reference to mdi container holding this widget
                                # Will be set up in the presenter, which arranges mdi windows for all MainWindow widgets
        self._view_geometry = None  # holder for slider view geometry, created to store slider view location
        # within the main window for subsequent calls to show sliders. Not yet restored from hdd properly
        # inherits project geometry on the first view.
        self._parent = parent  # reference to main view widget which holds sliders view

        self._values_to_revert ={}  # dictionary of values of original properties with fit parameter "true"
        # to be restored back into original project if cancel button is pressed.
        self._prop_to_change = {}  # dictionary of references to SliderUpdateHoler classes containing properties
        # with fit parameter "true" to build sliders for and allow changes when slider is moved.
        # Their values are reflected in project and affect plots.

        self._sliders = {}   # dictionary of the sliders used to display fittable values
        # create initial slider view layout and everything else which depends on it
        self.init()


    def show(self):
        """Overload parent show method to deal with mdi container
           showing sliders widget window. Also sets up or updates sliders
           widget list depending on previous state of the widget
        """

        # avoid running init view more than once if sliders are visible anyway
        if self.isVisible():
           return

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
           into dictionary used to build sliders for them. Also set back-up
           dictionary  to reset properties values back to their initial values if "Cancel"
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

        proj = self._parent.project_widget
        if proj is None:
            return False

        n_updated_properties = 0
        trial_properties = {}
        for widget in proj.view_tabs.values():
            for param in widget.tables.values():
                vis_model = param.model
                if isinstance(vis_model, ParametersModel):
                    row = 0
                    for model_param in vis_model.classlist:
                        if model_param.fit:
                            trial_properties[model_param.name] = SliderChangeHolder(row_number=row,model=vis_model,param=model_param)
                            if model_param.name in self._prop_to_change:
                                n_updated_properties += 1
                        row += 1

        # if all properties of trial dictionary are in existing dictionary and the number of properties are the same
        # no new/deleted sliders have appeared.
        # We will update widgets parameters instead of deleting old and creating the new one.
        update_properties = n_updated_properties == len(trial_properties) and len(self._prop_to_change) == n_updated_properties

        # store information about sliders
        self._prop_to_change = trial_properties
        # remember values for properties controlled by sliders in case if you may want to revert them later
        self._values_to_revert = {name: prop.value for name, prop in trial_properties.items()}

        return update_properties

    def _create_slider_view_layout(self) -> None:
        """ Create sliders layout with all necessary controls and connections
            but without sliders themselves.
        """

        main_layout = QtWidgets.QVBoxLayout()

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

        # We are adding new sliders, so delete all previous ones. Update is done in another branch.
        for slider in self._sliders.values():
            slider.deleteLater()
        self._sliders = {}

        if len(self._prop_to_change) == 0:
            no_label = EmptySlider()
            content_layout.addWidget(no_label)
            self._sliders[no_label.slider_name] = no_label
        else:
            content_layout.setSpacing(0)
            for name,prop in self._prop_to_change.items():
                slider = LabeledSlider(prop)

                self._sliders[prop.name] = slider
                content_layout.addWidget(slider)

    def _update_sliders_widgets(self) -> None:
        """Updates the sliders given the project properties to fit are the same
           but their values may be modified
        """
        for name,prop in self._prop_to_change.items():
            self._sliders[name].update_slider_parameters(prop)

    def show_sliders_view(self) -> None:
        """Show project view"""
        self._parent.show_or_hide_sliders(do_show_sliders=True)

    def _cancel_changes_from_sliders(self):
        """Cancel changes to properties obtained from sliders
           and hide sliders view.
        """
        if len(self._values_to_revert) == 0:
            last_key = None
        else:      # does not work with empty dictionary
            last_key = next(reversed(self._values_to_revert))


        for key,val in self._values_to_revert.items():
            self._sliders[key].set_slider_position(val)
            if key == last_key:
                self._prop_to_change[key].update_value_representation(val,recalculate_project=True)
            else:
                self._prop_to_change[key].update_value_representation(val,recalculate_project=False)

        self._parent.show_or_hide_sliders(do_show_sliders=False)

    def _apply_changes_from_sliders(self) -> None:
        """Apply changes obtained from sliders to the project
           and make them permanent
        """
        for key,prop in self._prop_to_change.items():
            self._values_to_revert[key] = prop.value

        self._parent.show_or_hide_sliders(False)
        return

#=======================================================================================================================
class SliderChangeHolder:
    """ Helper class containing information necessary for update
       ratapi parameter and its representation in project table view
       when slider position is changed
    """
    def __init__(self, row_number: int,model : ParametersModel, param : ratapi.models.Parameter) -> None:
        """ Class Initialization function:
        Inputs:
        ------
        row_number: int - the number of the row in the project table which should be changed
        model: rascal2.widgets.project.tables.ParametersModel - parameters model participating in ParametersTableView
               and containing the parameter (below) to modify here.
        param: ratapi.models.Parameter - the parameter which value field may be changed by slider widget
        """
        self.param = param
        self._vis_model   = model
        self._row_number = row_number
        self._param_value = param.value

    @property
    def name(self):
        return self.param.name

    @property
    def value(self) -> float:
        return self._param_value
    @value.setter
    def value(self, value: float) -> None:
        self._param_value = value
        setattr(self.param,"value",value)

    def update_value_representation(self,val : float, recalculate_project = True) -> None:
        """ given new value, update project table and property representations
            No check are necessary as value comes from slider or back-up cache

            recalculate_project -- if True, run ratapi calculations and updates
            results representation.
         """
        # value for ratapi parameter is defined in column 4 and this number is hardwired here
        # should be a better way of doing this.
        index = self._vis_model.index(self._row_number, 4)
        self._vis_model.setData(index, val, QtCore.Qt.ItemDataRole.EditRole,recalculate_project)
        # this is probably unnecessary, as have been already set through the model. But it's fast.
        self.param.value = val


class LabeledSlider(QtWidgets.QFrame):
    def __init__(self, param: SliderChangeHolder):
        """Construct LabeledSlider for a particular property
        Inputs:
        -------
        param       --  instance of the SliderChangeHolder class, containing reference to the property to be modified by
                        slider and the reference to visual model, which controls the position and the place of this
                        property in the correspondent project table.
        """
        super().__init__()

        self._prop = param  # hold the property controlled by slider

        # Defaults for property min/max. Will be overwritten from actual input property
        self._value_min : float   | None = 0     # minimal value property may have
        self._value_max : float   | None = 100   # maximal value property may have
        self._value_range : float | None = 100   # value range (difference between maximal and minimal values of the property)
        self._value_step : float  | None = 1     # the change in property value per single step slider move

        # Internal properties of slider widget:
        self._num_slider_ticks : int = 10
        self._slider_max_idx : int   = 100  # defines accuracy of slider motion
        self._ticks_step : int       = 10   # Number of sliders ticks
        self._labels : list          = []   # list of slider labels describing sliders axis
        self._value_label_format : str = "{:.4g}"  # format to display slider value. Should be not too accurate as slider is not very accurate.
        self._tick_label_format : str  = "{:.2g}"  # format to display numbers under the sliders ticks
        if param is None:
            return

        self.slider_name = param.name # name the slider as the property it refers to
        self.update_slider_parameters(param,in_constructor=True) # Retrieve slider's parameters from input property

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
        middle_val = self._value_min+0.5*self._value_range
        middle_min = middle_val - 0.5*tick_step
        middle_max = middle_val + 0.5*tick_step
        for idx in range(0,self._num_slider_ticks + 1):
            tick_value = self._value_min+idx*tick_step
            label = QtWidgets.QLabel(self._tick_label_format.format(tick_value))
            if tick_value < middle_min:
                label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
            elif tick_value > middle_max:
                label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            else:
                label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)

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

    def set_slider_position(self,value : float) -> None:
        """Set specified slider position programmatically """
        idx = self._value_to_slider_pos(value)
        self._slider.setValue(idx)
        self._value_label.setText(self._value_label_format.format(value))

    def update_slider_parameters(self, param: SliderChangeHolder, in_constructor = False):
        """Modifies slider values which may change for this slider from his parent property"""

        self._prop = param
        # Characteristics of the property value to display
        self._value_min = self._prop.param.min
        self._value_max = self._prop.param.max
        self._value_range = (self._value_max - self._value_min)
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
        value = self._value_min + index*self._value_step
        if value > self._value_max: # This should not happen but may due to round-off errors
            value = self._value_max
        return value

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
        self._prop.update_value_representation(val)


class EmptySlider(LabeledSlider):
    def __init__(self):
        """Construct empty slider which have interface of LabeledSlider but no properties
        associated with it
        Inputs:
        ------
        ignored
        """
        super().__init__(None)
        # Build all sliders widget and arrange them as expected
        self._slider = self._build_slider(0)

        name_label = QtWidgets.QLabel("No property to fit within the project. No sliders constructed", alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(name_label)
        self.slider_name = "Empty Slider"
        self.setObjectName(self.slider_name)

    def set_slider_position(self,value : float) -> None:
        return

    def update_slider_parameters(self, param: SliderChangeHolder, in_constructor = False):
        return

    def _build_slider(self,initial_value: float) -> QtWidgets.QSlider:
        return None

    def _update_value(self, idx: int)->None:
        return
