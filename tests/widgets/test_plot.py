from unittest.mock import MagicMock, patch

import pytest
import ratapi
from PyQt6 import QtWidgets

from rascal2.widgets.plot import (
    AbstractPanelPlotWidget,
    PlotWidget,
    RefSLDWidget,
    ShadedPlotWidget,
)


class MockWindowView(QtWidgets.QMainWindow):
    """A mock MainWindowView class."""

    def __init__(self):
        super().__init__()
        self.presenter = MagicMock()
        self.presenter.model = MagicMock()


view = MockWindowView()


@pytest.fixture
def plot_widget():
    plot_widget = PlotWidget(view)
    plot_widget.parent_model = MagicMock()
    plot_widget.reflectivity_plot = MagicMock()

    return plot_widget


@pytest.fixture
def sld_widget():
    sld_widget = RefSLDWidget(view)
    sld_widget.canvas = MagicMock()

    return sld_widget


@pytest.fixture
def shaded_plot_widget():
    shaded_plot_widget = ShadedPlotWidget(view)
    shaded_plot_widget.canvas = MagicMock()

    return shaded_plot_widget


@pytest.fixture
def mock_bayes_results():
    """A mock of Bayes results with given fit parameter names."""

    def _mock_bayes(fitnames):
        bayes_results = MagicMock(spec=ratapi.outputs.BayesResults)
        bayes_results.fitNames = fitnames

        return bayes_results

    return _mock_bayes


class MockPanelPlot(AbstractPanelPlotWidget):
    """A mock widget for panel plots."""

    def __init__(self, parent):
        super().__init__(parent)
        self.mock_plotter = MagicMock()

    def draw_plot(self):
        self.all_params = [
            self.param_combobox.model().item(i).data() for i in range(self.param_combobox.model().rowCount())
        ]
        self.plot_params = self.param_combobox.selected_items()

        self.mock_plotter()


def test_plot_widget_update_plots(plot_widget):
    """Test that the plots are updated correctly when update_plots is called."""
    plot_widget.update_plots(MagicMock(), MagicMock(spec=ratapi.outputs.Results))

    assert not plot_widget.bayes_plots_button.isVisibleTo(plot_widget)
    plot_widget.reflectivity_plot.plot.assert_called_once()
    plot_widget.reflectivity_plot.reset_mock()

    plot_widget.update_plots(MagicMock(), MagicMock(spec=ratapi.outputs.BayesResults))

    assert plot_widget.bayes_plots_button.isVisibleTo(plot_widget)
    plot_widget.reflectivity_plot.plot.assert_called_once()


def test_ref_sld_toggle_setting(sld_widget):
    """Test that plot settings are hidden when the button is toggled."""
    assert not sld_widget.plot_controls.isVisibleTo(sld_widget)
    sld_widget.toggle_button.toggle()
    assert sld_widget.plot_controls.isVisibleTo(sld_widget)
    sld_widget.toggle_button.toggle()
    assert not sld_widget.plot_controls.isVisibleTo(sld_widget)


@patch("ratapi.plotting.ratapi.plotting.plot_ref_sld_helper")
def test_ref_sld_plot_event(mock_plot_sld, sld_widget):
    """Test that plot helper recieved correct flags from UI."""
    data = ratapi.events.PlotEventData()
    data.contrastNames = ["Hello"]

    assert sld_widget.current_plot_data is None
    sld_widget.plot_event(data)
    assert sld_widget.current_plot_data is data
    mock_plot_sld.assert_called_with(
        data,
        sld_widget.figure,
        delay=False,
        linear_x=False,
        q4=False,
        show_error_bar=True,
        show_grid=False,
        show_legend=True,
        shift_value=1,
    )
    sld_widget.canvas.draw.assert_called_once()
    data.contrastNames = []
    sld_widget.plot_event(data)
    mock_plot_sld.assert_called_with(
        data,
        sld_widget.figure,
        delay=False,
        linear_x=False,
        q4=False,
        show_error_bar=True,
        show_grid=False,
        show_legend=False,
        shift_value=1,
    )
    data.contrastNames = ["Hello"]
    sld_widget.x_axis.setCurrentText("Linear")
    sld_widget.y_axis.setCurrentText("Q^4")
    sld_widget.show_error_bar.setChecked(False)
    sld_widget.show_grid.setChecked(True)
    sld_widget.show_legend.setChecked(False)
    mock_plot_sld.assert_called_with(
        data,
        sld_widget.figure,
        delay=False,
        linear_x=True,
        q4=True,
        show_error_bar=False,
        show_grid=True,
        show_legend=False,
        shift_value=1,
    )


@patch("ratapi.inputs.make_input")
def test_ref_sld_plot(mock_inputs, sld_widget):
    """Test that the plot is made when given a plot event."""
    project = MagicMock()
    result = MagicMock()
    data = MagicMock
    with patch("ratapi.events.PlotEventData", return_value=data):
        assert sld_widget.current_plot_data is None
        sld_widget.plot(project, result)
        assert sld_widget.current_plot_data is data
        sld_widget.canvas.draw.assert_called_once()


def test_param_combobox_items(mock_bayes_results):
    """Test that the parameter multi-select combobox items are the full set of fit parameters."""
    bayes_results = mock_bayes_results(["A", "B", "C"])

    widget = MockPanelPlot(view)
    widget.plot(None, bayes_results)

    assert widget.all_params == ["A", "B", "C"]

    bayes_results.fitNames = ["A", "D"]

    widget.plot(None, bayes_results)

    assert widget.all_params == ["A", "D"]


@pytest.mark.parametrize("init_select", ([], ["A", "C"], ["B"], ["A", "B", "C"]))
def test_param_combobox_select(mock_bayes_results, init_select):
    """Test that the select button correctly selects all parameters."""
    bayes_results = mock_bayes_results(["A", "B", "C"])

    widget = MockPanelPlot(view)
    widget.plot(None, bayes_results)
    widget.param_combobox.select_items(init_select)

    assert widget.param_combobox.selected_items() == init_select

    select_button = None
    buttons = widget.findChildren(QtWidgets.QPushButton)
    for button in buttons:
        if button.text() == "Select all":
            select_button = button
            break

    select_button.click()

    assert widget.param_combobox.selected_items() == ["A", "B", "C"]


@pytest.mark.parametrize("init_select", ([], ["A", "C"], ["B"], ["A", "B", "C"]))
def test_param_combobox_deselect(mock_bayes_results, init_select):
    """Test that the select button correctly selects all parameters."""
    bayes_results = mock_bayes_results(["A", "B", "C"])

    widget = MockPanelPlot(view)
    widget.plot(None, bayes_results)
    widget.param_combobox.select_items(init_select)

    assert widget.param_combobox.selected_items() == init_select

    deselect_button = None
    buttons = widget.findChildren(QtWidgets.QPushButton)
    for button in buttons:
        if button.text() == "Deselect all":
            deselect_button = button
            break

    deselect_button.click()

    assert widget.param_combobox.selected_items() == []
