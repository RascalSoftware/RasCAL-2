"""The Plot MDI widget."""

from abc import abstractmethod
from inspect import isclass

import matplotlib
import ratapi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import path_for
from rascal2.widgets.inputs import MultiSelectComboBox, ProgressButton


class PlotWidget(QtWidgets.QWidget):
    """The MDI plot widget."""

    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.parent.presenter.model.results_updated.connect(self.update_plots)

        layout = QtWidgets.QVBoxLayout()

        button_layout = QtWidgets.QHBoxLayout()
        self.bayes_plots_button = QtWidgets.QPushButton("View Bayes plots")
        self.bayes_plots_button.setVisible(False)
        self.bayes_plots_button.pressed.connect(self.show_bayes_plots)

        button_layout.addWidget(self.bayes_plots_button)
        button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.reflectivity_plot = RefSLDWidget(self)
        layout.addLayout(button_layout)
        layout.addWidget(self.reflectivity_plot)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 5, 0, 20)
        self.setLayout(layout)

    def update_plots(self):
        """Update the plot widget to match the parent model."""
        model = self.parent.presenter.model
        self.reflectivity_plot.plot(model.project, model.results)
        self.bayes_plots_button.setVisible(isinstance(model.results, ratapi.outputs.BayesResults))

    def plot_with_blit(self, event: ratapi.events.PlotEventData):
        """Handle plot event data.

        Parameters
        ----------
        event : ratapi.events.PlotEventData
            plot event data
        """
        self.reflectivity_plot.plot_with_blit(event)

    def show_bayes_plots(self):
        bayes_plots = BayesPlotsDialog(self.parent)
        bayes_plots.exec()

    def clear(self):
        """Clear the Ref/SLD canvas."""
        self.reflectivity_plot.clear()


class BayesPlotsDialog(QtWidgets.QDialog):
    """The modal dialog for the Bayes plots."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent_model = parent.presenter.model
        self.installEventFilter(self)
        self.resize_timer = 0

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowMaximizeButtonHint, True)

        layout = QtWidgets.QVBoxLayout()
        self.result_summary = QtWidgets.QLabel()
        self.result_summary.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.plot_tabs = QtWidgets.QTabWidget()

        plots = {
            "Shaded plot": ShadedPlotWidget,
            "Corner Plot": CornerPlotWidget,
            "Posteriors": HistPlotWidget,
            "Diagnostics": ChainPlotWidget,
        }

        for plot_type, plot_widget in plots.items():
            self.add_tab(plot_type, plot_widget)

        self.sync_and_update_model()
        layout.addWidget(self.result_summary)
        layout.addWidget(self.plot_tabs)
        self.setLayout(layout)
        self.setModal(True)
        self.resize(900, 600)
        self.setWindowTitle("Bayes Results")
        self.plot_tabs.currentChanged.connect(self.redraw_panel_plot)

    def add_tab(self, plot_type: str, plot_widget: "AbstractPlotWidget"):
        """Add a widget as a tab to the plot widget.

        Parameters
        ----------
        plot_type : str
            The name of the plot type.
        plot_widget : AbstractPlotWidget
            The plot widget to add as a tab.

        """
        # create widget instance if a widget class handle was given
        # rather than an instance
        if isclass(plot_widget):
            plot_widget = plot_widget(self)
            plot_widget.toggle_button.setChecked(True)

        self.plot_tabs.addTab(plot_widget, plot_type)

        if self.parent_model.results is not None:
            plot_widget.plot(self.parent_model.project, self.parent_model.results)

    def sync_and_update_model(self):
        """Set panel plot parameter comboboxes to the same model so changing parameters in one updates the others."""
        if self.parent_model.results is None:
            return

        model = QtGui.QStandardItemModel()
        model.dataChanged.connect(self.set_redraw_state)
        for i in range(1, 4):
            widget = self.plot_tabs.widget(i)
            widget.param_combobox.setModel(model)
            widget.redraw_plot = i != 1
        widget.param_combobox.addItems(self.parent_model.results.fitNames)
        widget.param_combobox.select_items(self.parent_model.results.fitNames)
        samples = self.parent_model.results.nestedSamplerOutput.nestSamples
        if samples.shape != (1, 2):
            self.result_summary.setText(
                f"log (Z) = {self.parent_model.results.nestedSamplerOutput.logZ:.5f}\n"
                f"log (Z) error = {self.parent_model.results.nestedSamplerOutput.logZErr:.5f}"
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.resize_timer != 0:
            self.killTimer(self.resize_timer)
            self.resize_timer = 0
        self.resize_timer = self.startTimer(500)

    def timerEvent(self, event):
        self.draw_current_panel_plot()
        self.killTimer(event.timerId())
        self.resize_timer = 0

    def eventFilter(self, _obj, event):
        if event.type() == QtCore.QEvent.Type.WindowStateChange:
            self.draw_current_panel_plot()
            return True
        return False

    def draw_current_panel_plot(self):
        """Draw the current panel plot (if not corner) when resizing"""
        if self.plot_tabs.currentIndex() > 1:
            self.plot_tabs.currentWidget().draw_plot()
        self.set_redraw_state()
        self.is_resizing = False

    def set_redraw_state(self):
        """Set the redraw state of not visible panel plots"""
        index = self.plot_tabs.currentIndex()
        self.plot_tabs.widget(2).redraw_plot = index != 2
        self.plot_tabs.widget(3).redraw_plot = index != 3

    def redraw_panel_plot(self):
        """Draw current panel plot if its redraw state is True"""
        widget = self.plot_tabs.currentWidget()
        if isinstance(widget, AbstractPanelPlotWidget) and widget.redraw_plot:
            widget.draw_plot()


class AbstractPlotWidget(QtWidgets.QWidget):
    """Widget to contain a plot and relevant settings."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.current_plot_data = None

        main_layout = QtWidgets.QHBoxLayout()

        plot_settings = self.make_control_layout()

        export_button = QtWidgets.QPushButton("Export plot...")
        export_button.pressed.connect(self.export)

        plot_settings.insertSpacing(0, 15)
        plot_settings.addStretch(1)
        plot_settings.addWidget(export_button)

        # self.plot_controls contains hideable controls
        self.plot_controls = QtWidgets.QWidget()
        self.plot_controls.setLayout(plot_settings)

        self.toggle_button = QtWidgets.QToolButton()
        self.toggle_button.toggled.connect(self.toggle_settings)
        self.toggle_button.setCheckable(True)
        self.toggle_settings(self.toggle_button.isChecked())

        # plot_toolbar contains always-visible toolbar
        plot_toolbar = QtWidgets.QVBoxLayout()
        plot_toolbar.addWidget(self.toggle_button)
        slider = self.make_toolbar_widget()
        if slider is None:
            plot_toolbar.addStretch(1)
        else:
            sub_layout = QtWidgets.QHBoxLayout()
            sub_layout.addStretch(1)
            sub_layout.addWidget(slider)
            sub_layout.addStretch(1)
            plot_toolbar.addLayout(sub_layout)
            plot_toolbar.addSpacing(15)

        sidebar = QtWidgets.QHBoxLayout()
        sidebar.addWidget(self.plot_controls)
        sidebar.addLayout(plot_toolbar)

        self.blit_plot = None
        self.figure = self.make_figure()
        self.canvas = FigureCanvas(
            self.figure,
        )
        self.figure.set_facecolor("none")
        self.canvas.setStyleSheet("background-color: transparent;")

        self.canvas.setParent(self)
        self.setMinimumSize(500, 300)

        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidget(self.canvas)
        scroll_area.setWidgetResizable(True)

        main_layout.addLayout(sidebar, 0)
        main_layout.addWidget(scroll_area, 4)
        self.setLayout(main_layout)

    def toggle_settings(self, toggled_on: bool):
        """Toggles the visibility of the plot controls"""
        self.plot_controls.setVisible(toggled_on)
        if toggled_on:
            self.toggle_button.setIcon(QtGui.QIcon(path_for("hide-settings.png")))
        else:
            self.toggle_button.setIcon(QtGui.QIcon(path_for("settings.png")))

    @abstractmethod
    def make_control_layout(self) -> QtWidgets.QLayout:
        """Make the plot control panel.

        Returns
        -------
        QtWidgets.QLayout
            The control panel layout for the plot.

        """
        raise NotImplementedError

    def make_toolbar_widget(self):
        """Make widgets for the toolbar."""

    def make_figure(self) -> matplotlib.figure.Figure:
        """Make the figure to plot onto.

        Returns
        -------
        Figure
            The figure to plot onto.

        """
        return matplotlib.figure.Figure(figsize=(9, 6))

    @abstractmethod
    def plot(self, project: ratapi.Project, results: ratapi.outputs.Results | ratapi.outputs.BayesResults):
        """Plot from the current project and results.

        Parameters
        ----------
        problem : ratapi.Project
            The project.
        results : Union[ratapi.outputs.Results, ratapi.outputs.BayesResults]
            The calculation results.

        """
        raise NotImplementedError

    def clear(self):
        """Clear the canvas."""
        self.figure.clear()
        self.canvas.draw()

    def export(self):
        """Save the figure to a file."""
        filepath, accepted = QtWidgets.QFileDialog.getSaveFileName(self, "Export Plot", filter="Image File (*.png)")
        if accepted:
            self.figure.savefig(filepath)


class RefSLDWidget(AbstractPlotWidget):
    """Creates a UI for displaying the path lengths from the simulation result"""

    def make_control_layout(self):
        self.plot_controls = QtWidgets.QWidget()
        self.x_axis = QtWidgets.QComboBox()
        self.x_axis.addItems(["Log", "Linear"])
        self.x_axis.currentTextChanged.connect(self.handle_control_changed)
        self.y_axis = QtWidgets.QComboBox()
        self.y_axis.addItems(["Ref", "Q^4"])
        self.y_axis.currentTextChanged.connect(self.handle_control_changed)
        self.show_error_bar = QtWidgets.QCheckBox("Show Error Bars")
        self.show_error_bar.setChecked(True)
        self.show_error_bar.checkStateChanged.connect(self.handle_control_changed)
        self.show_grid = QtWidgets.QCheckBox("Show Grid")
        self.show_grid.checkStateChanged.connect(self.handle_control_changed)
        self.show_legend = QtWidgets.QCheckBox("Show Legend")
        self.show_legend.setChecked(True)
        self.show_legend.checkStateChanged.connect(self.handle_control_changed)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("X-Axis"))
        layout.addWidget(self.x_axis)
        layout.addWidget(QtWidgets.QLabel("Y-Axis"))
        layout.addWidget(self.y_axis)
        layout.addWidget(self.show_error_bar)
        layout.addWidget(self.show_grid)
        layout.addWidget(self.show_legend)

        return layout

    def make_toolbar_widget(self):
        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Vertical)
        self.slider.setTracking(False)
        self.slider.setInvertedAppearance(True)
        self.slider.setMinimum(1)
        self.slider.setMaximum(100)
        self.slider.setValue(1)
        self.slider.valueChanged.connect(self.handle_control_changed)

        return self.slider

    def make_figure(self) -> matplotlib.figure.Figure:
        self.resize_timer = 0
        figure = matplotlib.figure.Figure()
        figure.subplots(1, 2)

        return figure

    def handle_control_changed(self):
        if self.blit_plot is None:
            self.plot_event()
        else:
            self.plot_with_blit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.resize_timer != 0:
            self.killTimer(self.resize_timer)
            self.resize_timer = 0
        self.resize_timer = self.startTimer(500)

    def timerEvent(self, event):
        if self.blit_plot is None:
            self.plot_event()
        self.killTimer(event.timerId())
        self.resize_timer = 0

    def plot(self, project: ratapi.Project, results: ratapi.outputs.Results | ratapi.outputs.BayesResults):
        """Plots the reflectivity and SLD profiles.

        Parameters
        ----------
        project : ratapi.Project
            The project
        results : Union[ratapi.outputs.Results, ratapi.outputs.BayesResults]
            The calculation results.
        """
        if project is None or results is None:
            self.clear()
            return

        data = ratapi.events.PlotEventData()

        data.modelType = project.model
        data.reflectivity = results.reflectivity
        data.shiftedData = results.shiftedData
        data.sldProfiles = results.sldProfiles
        data.resampledLayers = results.resampledLayers
        data.dataPresent = ratapi.inputs.make_data_present(project)
        data.subRoughs = results.contrastParams.subRoughs
        data.resample = ratapi.inputs.make_resample(project)
        data.contrastNames = [contrast.name for contrast in project.contrasts]
        self.plot_event(data)

    def plot_event(self, data: ratapi.events.PlotEventData | None = None):
        """Updates the ref and SLD plots from a provided or cached plot event

        Parameters
        ----------
        data : Optional[ratapi.events.PlotEventData]
            plot event data, cached data is used if none is provided
        """
        if self.blit_plot is not None:
            del self.blit_plot
            self.blit_plot = None

        if data is not None:
            self.current_plot_data = data

        if self.current_plot_data is None:
            return

        show_legend = self.show_legend.isChecked() if self.current_plot_data.contrastNames else False
        ratapi.plotting.plot_ref_sld_helper(
            self.current_plot_data,
            self.figure,
            delay=False,
            linear_x=self.x_axis.currentText() == "Linear",
            q4=self.y_axis.currentText() == "Q^4",
            show_error_bar=self.show_error_bar.isChecked(),
            show_grid=self.show_grid.isChecked(),
            show_legend=show_legend,
            shift_value=self.slider.value(),
        )
        self.figure.tight_layout(pad=1)
        self.canvas.draw()

    def plot_with_blit(self, data: ratapi.events.PlotEventData | None = None):
        """Updates the ref and SLD plots with blitting

        Parameters
        ----------
        data : ratapi.events.PlotEventData
            plot event data
        """
        if data is not None:
            self.current_plot_data = data

        if self.current_plot_data is None:
            return

        linear_x = self.x_axis.currentText() == "Linear"
        q4 = self.y_axis.currentText() == "Q^4"
        show_error_bar = self.show_error_bar.isChecked()
        show_grid = self.show_grid.isChecked()
        show_legend = self.show_legend.isChecked() if self.current_plot_data.contrastNames else False
        shift_value = self.slider.value()
        if self.blit_plot is None:
            self.blit_plot = ratapi.plotting.BlittingSupport(
                self.current_plot_data,
                self.figure,
                linear_x=linear_x,
                q4=q4,
                show_error_bar=show_error_bar,
                show_grid=show_grid,
                show_legend=show_legend,
                shift_value=shift_value,
            )
        else:
            self.blit_plot.linear_x = linear_x
            self.blit_plot.q4 = q4
            self.blit_plot.show_error_bar = show_error_bar
            self.blit_plot.show_grid = show_grid
            self.blit_plot.show_legend = show_legend
            self.blit_plot.shift_value = shift_value

            self.blit_plot.update(self.current_plot_data)


class ShadedPlotWidget(AbstractPlotWidget):
    """Widget for plotting a contour plot of two parameters."""

    def make_control_layout(self):
        control_layout = QtWidgets.QVBoxLayout()

        self.ci_param_box = QtWidgets.QComboBox(self)
        self.ci_param_box.addItems(["65%", "95%"])
        self.ci_param_box.currentTextChanged.connect(lambda: self.draw_plot())

        control_layout.addWidget(QtWidgets.QLabel("Confidence Interval"))
        control_layout.addWidget(self.ci_param_box)

        return control_layout

    def plot(self, project, results: ratapi.outputs.BayesResults):
        """Plot the shaded plot."""
        self.project = project
        self.results = results

        self.draw_plot()

    def draw_plot(self):
        """Plots the shaded reflectivity and SLD profiles."""
        self.clear()

        ratapi.plotting.plot_ref_sld(
            self.project,
            self.results,
            bayes=int(self.ci_param_box.currentText().strip("%")),
            fig=self.figure,
        )
        self.canvas.draw()


class AbstractPanelPlotWidget(AbstractPlotWidget):
    """Abstract base widget for plotting panels of parameters (corner plot, histograms, chains)

    These widgets all share a parameter multi-select box, so it is defined here.

    """

    def __init__(self, parent):
        super().__init__(parent)
        self.redraw_plot = False

    def make_control_layout(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)
        param_layout = QtWidgets.QVBoxLayout()
        param_layout.setSpacing(2)

        self.desc_label = QtWidgets.QLabel(
            "<h3>Select parameters to update plot or click the 'Select all' button to plot all parameters.</h3>"
        )
        self.desc_label.setWordWrap(True)
        self.param_combobox = MultiSelectComboBox()

        select_deselect_row = QtWidgets.QHBoxLayout()
        select_button = QtWidgets.QPushButton("Select all")
        select_button.pressed.connect(
            lambda: self.param_combobox.select_indices(list(range(self.param_combobox.model().rowCount())))
        )
        deselect_button = QtWidgets.QPushButton("Deselect all")
        deselect_button.pressed.connect(lambda: self.param_combobox.select_indices([]))
        select_deselect_row.addWidget(select_button)
        select_deselect_row.addWidget(deselect_button)

        self.update_label = QtWidgets.QLabel()
        layout.addWidget(self.update_label)
        param_layout.addWidget(QtWidgets.QLabel("Parameters"))
        param_layout.addWidget(self.param_combobox)
        param_layout.addLayout(select_deselect_row)
        layout.addWidget(self.desc_label)
        layout.addSpacing(20)
        layout.addLayout(param_layout)

        return layout

    def plot(self, _, results):
        self.results = results
        self.draw_plot()

    def update_ui(self, current, total):
        if current + 1 == total:
            self.update_label.setText("")
        else:
            self.update_label.setText(f"<b>Updating plot {current + 1} of {total}</b>")
        QtWidgets.QApplication.instance().processEvents()

    def draw_plot(self):
        raise NotImplementedError

    def resize_canvas(self):
        self.canvas.setMinimumSize(900, 600)

    def clear(self):
        self.canvas.figure.clear()
        self.canvas.draw()
        self.canvas.setMinimumSize(0, 0)
        self.canvas.resize(100, 100)


class CornerPlotWidget(AbstractPanelPlotWidget):
    """Widget for plotting corner plots."""

    def make_control_layout(self):
        layout = super().make_control_layout()

        smooth_row = QtWidgets.QHBoxLayout()
        smooth_row.addWidget(QtWidgets.QLabel("Apply smoothing"))
        self.smooth_checkbox = QtWidgets.QCheckBox()
        self.smooth_checkbox.setCheckState(QtCore.Qt.CheckState.Checked)
        smooth_row.addWidget(self.smooth_checkbox)

        self.plot_button = ProgressButton("Update Plot", "Creating plots")
        self.plot_button.pressed.connect(self.draw_plot)

        layout.addLayout(smooth_row)
        layout.addWidget(self.plot_button)

        self.desc_label.setText(
            "<h3>Select parameters or click the 'Select all' button, then click the 'Update Plot' button.</h3>"
        )

        self.param_combobox.selection_changed.connect(self.toggle_plot_button)

        return layout

    def toggle_plot_button(self):
        self.plot_button.setEnabled(len(self.param_combobox.selected_items()) != 0)

    def update_ui(self, current, total):
        self.plot_button.update_progress(current, total)
        QtWidgets.QApplication.instance().processEvents()

    def draw_plot(self):
        plot_params = self.param_combobox.selected_items()
        smooth = self.smooth_checkbox.checkState() == QtCore.Qt.CheckState.Checked

        if plot_params:
            self.plot_button.show_progress()
            QtWidgets.QApplication.instance().processEvents()

            self.resize_canvas()
            self.figure.set_visible(False)
            ratapi.plotting.plot_corner(
                self.results, params=plot_params, smooth=smooth, fig=self.figure, progress_callback=self.update_ui
            )
            self.figure.set_visible(True)
            self.canvas.draw()
            self.plot_button.hide_progress()
        else:
            self.clear()
            self.figure.set_visible(False)
        self.redraw_plot = False


class HistPlotWidget(AbstractPanelPlotWidget):
    """Widget for plotting Bayesian posterior panels."""

    def make_control_layout(self):
        layout = super().make_control_layout()
        self.param_combobox.selection_changed.connect(self.draw_plot)

        smooth_row = QtWidgets.QHBoxLayout()
        smooth_row.addWidget(QtWidgets.QLabel("Apply smoothing"))
        self.smooth_checkbox = QtWidgets.QCheckBox()
        self.smooth_checkbox.setCheckState(QtCore.Qt.CheckState.Checked)
        self.smooth_checkbox.toggled.connect(self.draw_plot)
        smooth_row.addWidget(self.smooth_checkbox)

        est_density_row = QtWidgets.QHBoxLayout()
        est_density_row.addWidget(QtWidgets.QLabel("Estimated density"))

        self.est_density_combobox = QtWidgets.QComboBox()

        # loop over items and data as `addItems` doesn't support item data
        for item, data in [("None", None), ("normal", "normal"), ("log-normal", "lognor"), ("KDE", "kernel")]:
            self.est_density_combobox.addItem(item, data)

        self.est_density_combobox.currentTextChanged.connect(self.draw_plot)

        est_density_row.addWidget(self.est_density_combobox)

        layout.addLayout(smooth_row)
        layout.addLayout(est_density_row)
        return layout

    def draw_plot(self):
        plot_params = self.param_combobox.selected_items()
        smooth = self.smooth_checkbox.checkState() == QtCore.Qt.CheckState.Checked
        est_dens = self.est_density_combobox.currentData()

        if plot_params:
            self.resize_canvas()
            self.figure.set_visible(False)
            ratapi.plotting.plot_hists(
                self.results,
                params=plot_params,
                smooth=smooth,
                estimated_density={"default": est_dens},
                fig=self.figure,
                progress_callback=self.update_ui,
            )
            self.figure.set_visible(True)
            self.canvas.draw()
        else:
            self.clear()
            self.figure.set_visible(False)
        self.redraw_plot = False


class ChainPlotWidget(AbstractPanelPlotWidget):
    """Widget for plotting a Bayesian chain panel."""

    def make_control_layout(self):
        layout = super().make_control_layout()
        self.param_combobox.selection_changed.connect(self.draw_plot)

        maxpoints_row = QtWidgets.QHBoxLayout()

        maxpoints_label = QtWidgets.QLabel("Maximum points")
        maxpoints_label.setToolTip(
            "The number of points to display in each chain, evenly distributed along the chain. Capped at 100000."
        )
        maxpoints_row.addWidget(maxpoints_label)

        self.maxpoints_box = QtWidgets.QSpinBox()
        self.maxpoints_box.setMaximum(100000)
        self.maxpoints_box.setMinimum(1)
        self.maxpoints_box.setValue(15000)
        self.maxpoints_box.valueChanged.connect(self.draw_plot)

        maxpoints_row.addWidget(self.maxpoints_box)

        layout.addLayout(maxpoints_row)

        return layout

    def draw_plot(self):
        plot_params = self.param_combobox.selected_items()
        maxpoints = self.maxpoints_box.value()

        if plot_params:
            self.resize_canvas()
            self.figure.set_visible(False)
            ratapi.plotting.plot_chain(
                self.results,
                params=plot_params,
                maxpoints=maxpoints,
                fig=self.figure,
                return_fig=True,
                progress_callback=self.update_ui,
            )
            self.figure.set_visible(True)
            self.canvas.draw()
        else:
            self.clear()
            self.figure.set_visible(False)
        self.redraw_plot = False
