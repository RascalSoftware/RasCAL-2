"""Widget for the Sliders View window."""

import ratapi
from PyQt6 import QtCore, QtGui, QtWidgets


class SliderViewWidget(QtWidgets.QWidget):
    """The slider view widget which allows user change fitted parameters with sliders."""

    def __init__(self, draft_project, parent):
        """Initialize widget.

        Parameters
        ----------
        draft_project: ratapi.Project
            A copy of the project that will be modified by slider
        parent: MainWindowView
            An instance of the MainWindowView
        """
        super().__init__()
        self._parent = parent
        self.draft_project = draft_project

        self._sliders = {}
        self.parameters = {}

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        self.accept_button = QtWidgets.QPushButton("Accept", self)
        self.accept_button.clicked.connect(self._apply_changes_from_sliders)

        cancel_button = QtWidgets.QPushButton("Cancel", self)
        cancel_button.clicked.connect(self._cancel_changes_from_sliders)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.accept_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)
        content = QtWidgets.QWidget()
        scroll.setWidget(content)
        self.slider_content_layout = QtWidgets.QVBoxLayout()
        content.setLayout(self.slider_content_layout)

        self.initialize()

    def initialize(self):
        """Populate parameters and slider from draft project."""
        self._init_parameters_for_sliders()
        self._add_sliders_widgets()

    def _init_parameters_for_sliders(self):
        """Extract fitted parameters from the draft project."""
        self.parameters.clear()

        for class_list in self.draft_project.values():
            if hasattr(class_list, "_class_handle") and class_list._class_handle is ratapi.models.Parameter:
                for parameter in class_list:
                    if parameter.fit:
                        self.parameters[parameter.name] = parameter

    def _add_sliders_widgets(self):
        """Add sliders to the layout."""
        # We are adding new sliders, so delete all previous ones.
        for slider in self._sliders.values():
            self.slider_content_layout.removeWidget(slider)
            slider.deleteLater()
        for _ in range(self.slider_content_layout.count()):
            w = self.slider_content_layout.takeAt(0).widget()
            if w is not None:
                w.deleteLater()
        self._sliders.clear()
        self.accept_button.setDisabled(not self.parameters)

        if not self.parameters:
            no_label = QtWidgets.QLabel(
                "There are no fitted parameters.\n "
                "Select parameters to fit in the project view to populate the slider view.",
                alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            )
            self.slider_content_layout.addWidget(no_label)
        else:
            self.slider_content_layout.setSpacing(0)
            for name, params in self.parameters.items():
                slider = LabeledSlider(params, self)

                self._sliders[name] = slider
                self.slider_content_layout.addWidget(slider)
            self.slider_content_layout.addStretch(1)

    def update_result_and_plots(self):
        project = ratapi.Project()
        vars(project).update(self.draft_project)
        results = self._parent.presenter.quick_run(project)
        self._parent.plot_widget.reflectivity_plot.plot(project, results)

    def _cancel_changes_from_sliders(self):
        """Revert changes to parameter values and close slider view."""
        self._parent.plot_widget.update_plots()
        self._parent.toggle_sliders()

    def _apply_changes_from_sliders(self):
        """
        Apply changes obtained from sliders to the project and close slider view.
        """
        self._parent.presenter.edit_project(self.draft_project)
        self._parent.toggle_sliders()


class LabeledSlider(QtWidgets.QFrame):
    def __init__(self, param, parent):
        """Create a LabeledSlider for a given RAT parameter

        Parameters
        ----------
        param : ratapi.models.Parameter
            The parameter which the slider updates.
        parent : SliderViewWidget
            The container for the slider widget.
        """

        super().__init__()
        self.parent = parent
        self._value_label_format: str = "{:.3g}"

        self.param = param

        self._slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._slider.setMinimum(0)
        self._slider.setMaximum(100)
        self._slider.setTickInterval(10)
        self._slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBothSides)
        self._slider.setValue(self._param_value_to_slider_value(self.param.value))

        # name of given slider can not change. It will be different slider with different name
        name_label = QtWidgets.QLabel(param.name, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self._value_label = QtWidgets.QLabel(
            self._value_label_format.format(self.param.value), alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        lab_layout = QtWidgets.QHBoxLayout()
        lab_layout.addWidget(name_label)
        lab_layout.addWidget(self._value_label)

        scale_layout = QtWidgets.QHBoxLayout()
        num_of_ticks = self._slider.maximum() // self._slider.tickInterval()
        tick_step = (self.param.max - self.param.min) / num_of_ticks
        self.labels = [self.param.min + i * tick_step for i in range(num_of_ticks + 1)]

        self.margins = [10, 10, 10, 15]  # left, top, right, bottom
        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(lab_layout)
        layout.addWidget(self._slider)
        layout.addLayout(scale_layout)
        layout.setContentsMargins(*self.margins)

        self._slider.valueChanged.connect(self._update_value)
        self.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed)

    def paintEvent(self, event):
        # Draws tick labels
        # Adapted from https://gist.github.com/wiccy46/b7d8a1d57626a4ea40b19c5dbc5029ff"""
        super().paintEvent(event)
        style = self._slider.style()
        painter = QtGui.QPainter(self)
        st_slider = QtWidgets.QStyleOptionSlider()
        st_slider.initFrom(self._slider)
        st_slider.orientation = self._slider.orientation()

        length = style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_SliderLength, st_slider, self._slider)
        available = style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_SliderSpaceAvailable, st_slider, self._slider)
        for i, label_value in enumerate(self.labels):
            value = i * (len(self.labels) - 1)
            value_label = self._value_label_format.format(label_value)

            # get the size of the label
            rect = painter.drawText(QtCore.QRect(), QtCore.Qt.TextFlag.TextDontPrint, value_label)

            if self._slider.orientation() == QtCore.Qt.Orientation.Horizontal:
                # I assume the offset is half the length of slider, therefore
                # + length//2
                x_loc = (
                    QtWidgets.QStyle.sliderPositionFromValue(
                        self._slider.minimum(), self._slider.maximum(), value, available
                    )
                    + length // 2
                )

                # left bound of the text = center - half of text width + L_margin
                left = x_loc - rect.width() // 2 + self.margins[0]
                bottom = self.rect().bottom() - 5

                # enlarge margins if clipping
                if value == self._slider.minimum():
                    if left <= 0:
                        self.margins[0] = rect.width() // 2 - x_loc
                    if self.margins[3] <= rect.height():
                        self.margins[3] = rect.height()

                    self.layout().setContentsMargins(*self.margins)

                if value == self._slider.maximum() and rect.width() // 2 >= self.margins[2]:
                    self.margins[2] = rect.width() // 2
                    self.layout().setContentsMargins(*self.margins)

                pos = QtCore.QPoint(left, bottom)
                painter.drawText(pos, value_label)

    def _param_value_to_slider_value(self, param_value: float) -> int:
        """Convert parameter value into slider value.

        Parameters:
        -----------
        param_value : float
            parameter value

        Returns:
        --------
        value : int
            slider value that corresponds to the parameter value
        """
        param_value_range = self.param.max - self.param.min
        if abs(param_value_range) < 10e-7:
            return self._slider.maximum()
        return int(round(self._slider.maximum() * (param_value - self.param.min) / param_value_range, 0))

    def _slider_value_to_param_value(self, value: int) -> float:
        """Convert slider value into parameter value.

        Parameters
        ----------
        value : int
          slider value

        Returns
        -------
        param_value : float
            parameter value that corresponds to slider value
        """

        value_step = (self.param.max - self.param.min) / self._slider.maximum()
        param_value = self.param.min + value * value_step
        if param_value > self.param.max:  # This should not happen but do occur due to round-off errors
            param_value = self.param.max
        return param_value

    def _update_value(self, value: int):
        """Update parameter value and plot when slider value is changed.

        Parameters
        ----------
        value : int
            slider value

        """
        param_value = self._slider_value_to_param_value(value)
        self._value_label.setText(self._value_label_format.format(param_value))
        self.param.value = param_value
        self.parent.update_result_and_plots()
