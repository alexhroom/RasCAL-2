from unittest.mock import MagicMock, patch

import pytest
import RATapi
from PyQt6 import QtWidgets

from rascal2.widgets.plot import RefSLDWidget


class MockWindowView(QtWidgets.QMainWindow):
    """A mock MainWindowView class."""

    def __init__(self):
        super().__init__()
        self.presenter = MagicMock()
        self.presenter.model = MagicMock()


view = MockWindowView()


@pytest.fixture
def sld_widget():
    sld_widget = RefSLDWidget(view)
    sld_widget.canvas = MagicMock()

    return sld_widget


def test_ref_sld_toggle_setting(sld_widget):
    """Test that plot settings are hidden when the button is toggled."""
    assert not sld_widget.plot_controls.isVisibleTo(sld_widget)
    sld_widget.toggle_button.toggle()
    assert sld_widget.plot_controls.isVisibleTo(sld_widget)
    sld_widget.toggle_button.toggle()
    assert not sld_widget.plot_controls.isVisibleTo(sld_widget)


@patch("RATapi.plotting.RATapi.plotting.plot_ref_sld_helper")
def test_ref_sld_plot_event(mock_plot_sld, sld_widget):
    """Test that plot helper recieved correct flags from UI ."""
    data = RATapi.events.PlotEventData()
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
    )


@patch("RATapi.inputs.make_input")
def test_ref_sld_plot(mock_inputs, sld_widget):
    """Test that the plot is made when given a plot event."""
    project = MagicMock()
    result = MagicMock()
    data = MagicMock
    with patch("RATapi.events.PlotEventData", return_value=data):
        assert sld_widget.current_plot_data is None
        sld_widget.plot(project, result)
        assert sld_widget.current_plot_data is data
        sld_widget.canvas.draw.assert_called_once()
