"""Widget for the Sliders View window."""

import ratapi.models
from PyQt6 import QtCore, QtWidgets

from rascal2.widgets.project.tables import ParametersModel


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
        # within the main window for subsequent calls to show sliders. Not yet restored from hdd properly
        # inherits project geometry on the first view.
        self._parent = parent  # reference to main view widget which holds sliders view

        self._values_to_revert = {}  # dictionary of values of original properties with fit parameter "true"
        # to be restored back into original project if cancel button is pressed.
        self._prop_to_change = {}  # dictionary of references to SliderChangeHolder classes containing properties
        # with fit parameter "true" to build sliders for and allow changes when slider is moved.
        # Their values are reflected in project and affect plots.

        self._sliders = {}  # dictionary of the sliders used to display fittable values.

        self.__accept_button = None  # Placeholder for accept button indicating particular. Presence indicates
        # initial stage of widget construction was completed
        self.__sliders_widgets_layout = None  # Placeholder for the area, containing sliders widgets.
        # presence indicates advanced stage of slider widget construction was completed and sliders widgets
        # cam be propagated.

        # create initial slider view layout and everything else which depends on it
        self.init()

    def show(self):
        """Overload parent show method sets up or updates sliders
        list depending on previous state of the widget.
        """

        # avoid running init view more than once if sliders are visible.
        if self.isVisible():
            return

        self.init()
        super().show()

    def init(self) -> None:
        """Initializes general contents (buttons) of the sliders widget if they have not been initialized.

        If project is defined extracts properties, used to build sliders and generate list of sliders
         widgets to control the properties.
        """
        if self.__accept_button is None:
            self._create_slider_view_layout()

        if self._parent.presenter.model.project is None:
            return  # Project may be not initialized at all so project gui is not initialized

        update_sliders = self._init_properties_for_sliders()
        if update_sliders:
            self._update_sliders_widgets()
        else:
            self._add_sliders_widgets()

    def _init_properties_for_sliders(self) -> bool:
        """Loop through project's widget view tabs and models associated with them and extract
        properties used by sliders widgets.

        Select all ParametersModel-s and copy all their properties which have attribute
         "Fit" == True into dictionary used to build sliders for them. Also set back-up
        dictionary  to reset properties values back to their initial values if "Cancel"
        button is pressed.

        Requests:   SlidersViewWidget with initialized Project.

        Returns
        --------
        bool
            true if all properties in the project have already had sliders, generated for them
            earlier so we may update existing widgets instead of generating new ones.

        Sets up dictionary of slider parameters used to define sliders and sets up connections
            necessary to interact with table view, namely:

            1) slider to table and update graphics -> in the dictionary of slider parameters
            2) change from Table view delegates -> routine which modifies sliders view.
        """

        proj = self._parent.project_widget
        if proj is None:
            return False

        n_updated_properties = 0
        trial_properties = {}

        for widget in proj.view_tabs.values():
            for table_view in widget.tables.values():
                if not hasattr(table_view, "model"):
                    continue  # usually in tests when table view model is not properly established for all tabs
                data_model = table_view.model
                if not isinstance(data_model, ParametersModel):
                    continue  # data may be empty

                for row, model_param in enumerate(data_model.classlist):
                    if model_param.fit:
                        # Store information about necessary property and the model, which contains the property.
                        # The model is the source of methods which modify dependent table and force project
                        # recalculation.
                        trial_properties[model_param.name] = SliderChangeHolder(
                            row_number=row, model=data_model, param=model_param
                        )

                        if model_param.name in self._prop_to_change:
                            n_updated_properties += 1

        # if all properties of trial dictionary are in existing dictionary and the number of properties are the same
        # no new/deleted sliders have appeared.
        # We will update widgets parameters instead of deleting old and creating the new one.
        update_properties = (
            n_updated_properties == len(trial_properties)
            and len(self._prop_to_change) == n_updated_properties
            and n_updated_properties != 0
        )

        # store information about sliders properties
        self._prop_to_change = trial_properties
        # remember current values of properties controlled by sliders in case you want to revert them back later
        self._values_to_revert = {name: prop.value for name, prop in trial_properties.items()}

        return update_properties

    def _create_slider_view_layout(self) -> None:
        """Create sliders layout with all necessary controls and connections
        but without sliders themselves.
        """

        main_layout = QtWidgets.QVBoxLayout()

        accept_button = QtWidgets.QPushButton("Accept", self, objectName="AcceptButton")
        accept_button.clicked.connect(self._apply_changes_from_sliders)
        self.__accept_button = accept_button

        cancel_button = QtWidgets.QPushButton("Cancel", self, objectName="CancelButton")
        cancel_button.clicked.connect(self._cancel_changes_from_sliders)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        button_layout.addWidget(accept_button)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _add_sliders_widgets(self) -> None:
        """Given sliders view layout and list of properties which can be controlled by sliders
        add appropriate sliders to sliders view Widget
        """

        if self.__sliders_widgets_layout is None:
            main_layout = self.layout()
            scroll = QtWidgets.QScrollArea()
            scroll.setWidgetResizable(True)  # important: resize content to fit area
            main_layout.addWidget(scroll)
            content = QtWidgets.QWidget()
            scroll.setWidget(content)
            # --- Add content layout
            content_layout = QtWidgets.QVBoxLayout(content)
            self.__sliders_widgets_layout = content_layout
        else:
            content_layout = self.__sliders_widgets_layout

        # We are adding new sliders, so delete all previous ones. Update is done in another routine.
        for slider in self._sliders.values():
            slider.deleteLater()
        self._sliders = {}

        if len(self._prop_to_change) == 0:
            no_label = EmptySlider()
            content_layout.addWidget(no_label)
            self._sliders[no_label.slider_name] = no_label
        else:
            content_layout.setSpacing(0)
            for name, prop in self._prop_to_change.items():
                slider = LabeledSlider(prop)
                slider.setMaximumHeight(100)

                self._sliders[name] = slider
                content_layout.addWidget(slider, alignment=QtCore.Qt.AlignmentFlag.AlignTop)

    def _update_sliders_widgets(self) -> None:
        """
        Updates the sliders given the project properties to fit are the same but their values may be modified
        """
        for name, prop in self._prop_to_change.items():
            self._sliders[name].update_slider_parameters(prop)

    def _cancel_changes_from_sliders(self):
        """Revert changes to values of properties, controlled and modified by sliders
        to their initial values and hide sliders view.
        """

        changed_properties = self._identify_changed_properties()
        if len(changed_properties) > 0:
            last_changed_prop_num = len(changed_properties) - 1
            for prop_num, (name, val) in enumerate(self._values_to_revert.items()):
                self._prop_to_change[name].update_value_representation(
                    val,
                    recalculate_project=(prop_num == last_changed_prop_num),  # it is important to update project for
                    # last changed property only not to recalculate project multiple times.
                )
        # else: all properties value remain the same so no point in reverting to them
        self._parent.show_or_hide_sliders(do_show_sliders=False)

    def _identify_changed_properties(self) -> dict:
        """Identify properties changed by sliders from initial sliders state.

        Returns
        -------
         :dict
            dictionary of the original values for properties changed by sliders.
        """

        changed_properties = {}
        for prop_name, value in self._values_to_revert.items():
            if value != self._prop_to_change[prop_name].value:
                changed_properties[prop_name] = value
        return changed_properties

    def _apply_changes_from_sliders(self) -> None:
        """
        Apply changes obtained from sliders to the project  and make them permanent
        """
        # Changes have already been applied so just hide sliders widget
        self._parent.show_or_hide_sliders(do_show_sliders=False)
        return


class SliderChangeHolder:
    """Helper class containing information necessary for update ratapi parameter and its representation
    in project table view  when slider position is changed.
    """

    def __init__(self, row_number: int, model: ParametersModel, param: ratapi.models.Parameter) -> None:
        """Class Initialization function:

        Parameters
        ----------
        row_number: int
         the number of the row in the project table, which should be changed
        model: rascal2.widgets.project.tables.ParametersModel
          parameters model (in QT sense) participating in ParametersTableView
          and containing the parameter (below) to modify here.
        param: ratapi.models.Parameter
         the parameter which value field may be changed by slider widget
        """
        self.param = param
        self._vis_model = model
        self._row_number = row_number

    @property
    def name(self):
        return self.param.name

    @property
    def value(self) -> float:
        return self.param.value

    @value.setter
    def value(self, value: float) -> None:
        self.param.value = value

    def update_value_representation(self, val: float, recalculate_project=True) -> None:
        """given new value, updates project table and property representations in the tables

        No checks are necessary as value comes from slider or undo cache

        Parameters
        ----------
        val: float
            new value to set up slider position according to the slider's numerical scale
            (recalculated into actual integer position)
        recalculate_project: bool
            if True, run ratapi calculations and update representation of results in all dependent widgets.
            if False, just update tables and properties
        """
        # value for ratapi parameter is defined in column 4 and this number is hardwired here
        # should be a better way of doing this.
        index = self._vis_model.index(self._row_number, 4)
        self._vis_model.setData(index, val, QtCore.Qt.ItemDataRole.EditRole, recalculate_project)


class LabeledSlider(QtWidgets.QFrame):
    """Class describes slider widget which  allows modifying rascal property value and its representation
    in project table view.

    It also connects with table view and accepts changes in min/max/value
    obtained from  property.
    """

    # Class attributes of slider widget which usually remain the same for all classes.
    # Affect all sliders behaviour so are global.
    _num_slider_ticks: int = 10
    _slider_max_idx: int = 100  # defines accuracy of slider motion
    _ticks_step: int = 10  # Number of sliders ticks
    _value_label_format: str = (
        "{:.4g}"  # format to display slider value. Should be not too accurate as slider accuracy is 1/100
    )
    _tick_label_format: str = "{:.2g}"  # format to display numbers under the sliders ticks

    def __init__(self, param: SliderChangeHolder):
        """Construct LabeledSlider for a particular property

        Parameters
        ----------
        param: SliceChangeHolder
               instance of the SliderChangeHolder class, containing reference to the property to be modified by
               slider and the reference to visual model, which controls the position and the place of this
               property in the correspondent project table.
        """

        super().__init__()
        # Defaults for property min/max. Will be overwritten from actual input property
        self._value_min = 0  # minimal value property may have
        self._value_max = 100  # maximal value property may have
        self._value = 50  # cache for property value
        self._value_range = 100  # difference between maximal and minimal values of the property
        self._value_step = 1  # the change in property value per single step slider move

        self._prop = param  # hold the property controlled by slider
        if param is None:
            return

        self._labels = []  # list of slider labels describing sliders axis
        self.__block_slider_value_changed_signal = False

        self.slider_name = param.name  # name the slider as the property it refers to. Sets up once here.
        self.update_slider_parameters(param, in_constructor=True)  # Retrieve slider's parameters from input property

        # Build all sliders widget and arrange them as expected
        self._slider = self._build_slider(param.value)

        # name of given slider can not change. It will be different slider with different name
        name_label = QtWidgets.QLabel(self.slider_name, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self._value_label = QtWidgets.QLabel(
            self._value_label_format.format(self._value), alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        lab_layout = QtWidgets.QHBoxLayout()
        lab_layout.addWidget(name_label)
        lab_layout.addWidget(self._value_label)

        # layout for numeric scale below
        scale_layout = QtWidgets.QHBoxLayout()

        tick_step = self._value_range / self._num_slider_ticks
        middle_val = self._value_min + 0.5 * self._value_range
        middle_min = middle_val - 0.5 * tick_step
        middle_max = middle_val + 0.5 * tick_step
        for idx in range(0, self._num_slider_ticks + 1):
            tick_value = (
                self._value_min + idx * tick_step
            )  # it is not _slider_idx_to_value as tick step there is different
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

        # signal to update label dynamically and change all dependent properties
        self._slider.valueChanged.connect(self._update_value)

        self.setObjectName(self.slider_name)
        self.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.setMaximumHeight(self._slider.height())

    def set_slider_gui_position(self, value: float) -> None:
        """Set specified slider GUI position programmatically.

        As value assumed to be already correct, block signal
        for change, associated with slider position change in GUI

        Parameters
        ----------
            value: float
                new float value of the slider
        """
        self._value = value
        self._value_label.setText(self._value_label_format.format(value))

        idx = self._value_to_slider_pos(value)
        self.__block_slider_value_changed_signal = True
        self._slider.setValue(idx)
        self.__block_slider_value_changed_signal = False

    def update_slider_parameters(self, param: SliderChangeHolder, in_constructor=False):
        """Modifies slider values which may change for this slider from his parent property

        Parameters
        ----------
        param: SliderChangeHolder
            instance of the SliderChangeHolder class, containing updated values for the slider
        in_constructor: bool,default False
            logical value, indicating that the method is invoked in constructor. If true,
            some additional initialization will be performed.
        """
        self._prop = param
        # Changing RASCAL property this slider modifies is currently prohibited,
        # as property connected through table model and project parameters:
        if self._prop.name != self.slider_name:
            # This should not happen but if it is, ensure failure. Something wrong with logic.
            raise RuntimeError("Existing slider may be responsible for only one property")
        self.update_slider_display_from_property(in_constructor)

    def update_slider_display_from_property(self, in_constructor: bool) -> None:
        """Change internal sliders parameters and their representation in GUI
        if property, underlying sliders parameters have changed.

        Bound to event received from delegate when table values are changed.

        Parameters
        ----------
        in_constructor: bool,default False
            logical value, indicating that the method is invoked in constructor. If True,
            avoid change in graphics as these changes + graphics initialization
            will be performed separately.
        """
        # note the order of methods in comparison. Should be as here, as may break
        # property updates in constructor otherwise.
        if not (self._updated_from_rascal_property() or in_constructor):
            return

        self._value_range = self._value_max - self._value_min
        # the change in property value per single step slider move
        self._value_step = self._value_range / self._slider_max_idx

        if in_constructor:
            return
        # otherwise, update slider's labels
        self.set_slider_gui_position(self._value)
        tick_step = self._value_range / self._num_slider_ticks
        for idx in range(0, self._num_slider_ticks + 1):
            tick_value = self._value_min + idx * tick_step
            self._labels[idx].setText(self._tick_label_format.format(tick_value))

    def _updated_from_rascal_property(self) -> bool:
        """Check if rascal property values related to slider widget have changed
        and update them accordingly

        Returns:
        -------
            True if change detected and False otherwise
        """
        updated = False
        if self._value_min != self._prop.param.min:
            self._value_min = self._prop.param.min
            updated = True
        if self._value_max != self._prop.param.max:
            self._value_max = self._prop.param.max
            updated = True
        if self._value != self._prop.param.value:
            self._value = self._prop.param.value
            updated = True
        return updated

    def _value_to_slider_pos(self, value: float) -> int:
        """Convert double (property) value into slider position

        Parameters:
        -----------
            value : float
                double value within slider's min-max range to identify integer
                position corresponding to this value

        Returns:
        --------
              index : int
              integer position within 0-self._slider_max_idx range corresponding to input value
        """
        return int(round(self._slider_max_idx * (value - self._value_min) / self._value_range, 0))

    def _slider_pos_to_value(self, index: int) -> float:
        """Convert slider GUI position (index) into double property value

        Parameters
        ----------
            index : int
              integer position within 0-self._slider_max_idx range to process

        Returns
        -------
              value : float
                double value within slider's min-max range corresponding to input index
        """

        value = self._value_min + index * self._value_step
        if value > self._value_max:  # This should not happen but do occur due to round-off errors
            value = self._value_max
        return value

    def _build_slider(self, initial_value: float) -> QtWidgets.QSlider:
        """Construct slider widget with integer scales and ticks in integer positions

        Part of slider constructor

        Parameters
        ----------
            value : float
                double value within slider's min-max range to identify integer
                position corresponding to this value.

        Returns
        -------
              QtWidgets.QSlider instance
              with settings, corresponding to input parameters.
        """

        slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(self._slider_max_idx)
        slider.setTickInterval(self._ticks_step)
        slider.setSingleStep(self._slider_max_idx)
        slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBothSides)
        slider.setValue(self._value_to_slider_pos(initial_value))

        return slider

    def _update_value(self, idx: int) -> None:
        """Method which converts slider position into double property value
        and informs all dependent clients about this.

        Bound in constructor to GUI slider position changed event

        Parameters
        ----------
            idx : int
                integer position of slider deal in GUI

        """
        if self.__block_slider_value_changed_signal:
            return
        val = self._slider_pos_to_value(idx)
        self._value = val
        self._value_label.setText(self._value_label_format.format(val))

        self._prop.update_value_representation(val)
        # This should not be necessary as already done through setter above
        self._prop.param.value = val  # but fast and nice for tests


class EmptySlider(LabeledSlider):
    def __init__(self):
        """Construct empty slider which have interface of LabeledSlider but no properties
        associated with it

        Parameters
        ----------
            All input parameters are ignored
        """
        super().__init__(None)

        name_label = QtWidgets.QLabel(
            "There are no fitted parameters.\n"
            " Select parameters to fit in the project view to populate the sliders view.",
            alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
        )
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(name_label)
        self.slider_name = "Empty Slider"
        self.setObjectName(self.slider_name)

    def set_slider_gui_position(self, value: float) -> None:
        return

    def update_slider_parameters(self, param: SliderChangeHolder, in_constructor=False):
        return

    def update_slider_display_from_property(self, in_constructor: bool) -> None:
        return
