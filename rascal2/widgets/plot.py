"""The Plot MDI widget."""

from abc import abstractmethod
from functools import partial
from inspect import isclass
from typing import Optional, Union

import RATapi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import path_for


class PlotWidget(QtWidgets.QWidget):
    """The MDI widget for plotting."""

    def __init__(self, parent):
        super().__init__(parent)

        self.parent_model = parent.presenter.model
        self.parent_model.results_updated.connect(lambda: self.update_plots())

        layout = QtWidgets.QVBoxLayout()

        menu_layout = QtWidgets.QHBoxLayout()
        menu_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        add_plot_button = QtWidgets.QPushButton("Add Plot...")
        add_plot_menu = QtWidgets.QMenu()
        add_plot_button.setMenu(add_plot_menu)

        plot_types = {
            "Corner Plot": QtWidgets.QLabel("Not yet implemented"),  # CornerPlotWidget,
            "Posterior Plot": QtWidgets.QLabel("Not yet implemented"),  # HistPlotWidget,
            "Contour Plot": ContourPlotWidget,
            "Chain Plot": QtWidgets.QLabel("Not yet implemented"),  # ChainPlotWidget,
        }

        for plot_type, plot_widget in plot_types.items():
            action = QtGui.QAction(plot_type, self)
            action.triggered.connect(partial(self.add_tab, plot_type=plot_type, plot_widget=plot_widget))
            add_plot_menu.addAction(action)

        menu_layout.addWidget(add_plot_button)
        layout.addLayout(menu_layout)

        self.plot_tabs = QtWidgets.QTabWidget()
        self.plot_tabs.setTabsClosable(True)
        self.plot_tabs.tabCloseRequested.connect(lambda index: self.plot_tabs.removeTab(index) if index != 0 else None)

        layout.addWidget(self.plot_tabs)

        self.setLayout(layout)
        self.reflectivity_plot = RefSLDWidget(self)
        self.add_tab("Reflectivity", self.reflectivity_plot)
        # make reflectivity tab uncloseable
        # close button is apparently on left side on mac and right side on windows/linux...
        # so make both unclickable to be safe
        r_button = self.plot_tabs.tabBar().tabButton(0, QtWidgets.QTabBar.ButtonPosition.RightSide)
        l_button = self.plot_tabs.tabBar().tabButton(0, QtWidgets.QTabBar.ButtonPosition.LeftSide)
        if r_button is not None:
            r_button.resize(0, 0)
        if l_button is not None:
            l_button.resize(0, 0)

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

        new_tab_index = self.plot_tabs.count()
        self.plot_tabs.addTab(plot_widget, plot_type)
        plot_widget.tab_name_box.setText(plot_type)
        plot_widget.tab_name_box.textEdited.connect(
            lambda s: self.plot_tabs.setTabText(new_tab_index, (s or plot_type))
        )

    def update_plots(self):
        """Update all plots to current model results."""
        for i in range(0, self.plot_tabs.count()):
            self.plot_tabs.widget(i).plot(self.parent_model.project, self.parent_model.results)

    def plot_event(self, event):
        """Handle plot event data."""
        self.reflectivity_plot.plot_event(event)

    def clear(self):
        """Clear all canvases."""
        for i in range(0, self.plot_tabs.count()):
            self.plot_tabs.widget(i).clear()


class AbstractPlotWidget(QtWidgets.QWidget):
    """Widget to contain a plot and relevant settings."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.current_plot_data = None

        main_layout = QtWidgets.QHBoxLayout()

        sidebar = QtWidgets.QVBoxLayout()

        self.plot_controls = QtWidgets.QWidget()
        plot_controls_layout = self.make_control_layout()
        self.plot_controls.setLayout(plot_controls_layout)

        top_tab = QtWidgets.QHBoxLayout()
        self.tab_name_box = QtWidgets.QLineEdit()
        self.toggle_button = QtWidgets.QToolButton()
        self.toggle_button.toggled.connect(self.toggle_settings)
        self.toggle_button.setCheckable(True)
        self.toggle_settings(self.toggle_button.isChecked())

        top_tab.addWidget(self.tab_name_box)
        top_tab.addWidget(self.toggle_button)

        top_tab.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        sidebar.addLayout(top_tab)
        sidebar.addWidget(self.plot_controls)

        self.figure = self.make_figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        self.setMinimumHeight(300)

        main_layout.addLayout(sidebar, 0)
        main_layout.addWidget(self.canvas, 4)
        self.setLayout(main_layout)

    def toggle_settings(self, toggled_on: bool):
        """Toggles the visibility of the plot controls"""
        self.plot_controls.setVisible(toggled_on)
        self.tab_name_box.setVisible(toggled_on)
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

    @abstractmethod
    def make_figure(self) -> Figure:
        """Make the figure to plot onto.

        Returns
        -------
        Figure
            The figure to plot onto.

        """
        fig = Figure()
        fig.subplots(1, 1)
        return fig

    @abstractmethod
    def plot(self, project: RATapi.Project, results: Union[RATapi.outputs.Results, RATapi.outputs.BayesResults]):
        """Plot from the current project and results.

        Parameters
        ----------
        problem : RATapi.Project
            The project.
        results : Union[RATapi.outputs.Results, RATapi.outputs.BayesResults]
            The calculation results.

        """
        raise NotImplementedError

    def clear(self):
        """Clear the canvas."""
        for axis in self.figure.axes:
            axis.clear()
        self.canvas.draw()


class RefSLDWidget(AbstractPlotWidget):
    """Creates a UI for displaying the path lengths from the simulation result"""

    def make_control_layout(self):
        control_layout = QtWidgets.QHBoxLayout()

        self.plot_controls = QtWidgets.QWidget()
        self.x_axis = QtWidgets.QComboBox()
        self.x_axis.addItems(["Log", "Linear"])
        self.x_axis.currentTextChanged.connect(lambda: self.plot_event())
        self.y_axis = QtWidgets.QComboBox()
        self.y_axis.addItems(["Ref", "Q^4"])
        self.y_axis.currentTextChanged.connect(lambda: self.plot_event())
        self.show_error_bar = QtWidgets.QCheckBox("Show Error Bars")
        self.show_error_bar.setChecked(True)
        self.show_error_bar.checkStateChanged.connect(lambda: self.plot_event())
        self.show_grid = QtWidgets.QCheckBox("Show Grid")
        self.show_grid.checkStateChanged.connect(lambda: self.plot_event())
        self.show_legend = QtWidgets.QCheckBox("Show Legend")
        self.show_legend.setChecked(True)
        self.show_legend.checkStateChanged.connect(lambda: self.plot_event())

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("X-Axis"))
        layout.addWidget(self.x_axis)
        layout.addWidget(QtWidgets.QLabel("Y-Axis"))
        layout.addWidget(self.y_axis)
        layout.addWidget(self.show_error_bar)
        layout.addWidget(self.show_grid)
        layout.addWidget(self.show_legend)
        layout.addStretch(1)
        self.plot_controls.setLayout(layout)

        control_layout.addWidget(self.plot_controls)

        slider_layout = QtWidgets.QVBoxLayout()
        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Vertical)
        slider_layout.addWidget(self.slider)
        slider_layout.setAlignment(self.slider, QtCore.Qt.AlignmentFlag.AlignHCenter)
        control_layout.addLayout(slider_layout)

        return control_layout

    def make_figure(self) -> Figure:
        figure = Figure()
        figure.subplots(1, 2)

        return figure

    def plot(self, project: RATapi.Project, results: Union[RATapi.outputs.Results, RATapi.outputs.BayesResults]):
        """Plots the reflectivity and SLD profiles.

        Parameters
        ----------
        problem : RATapi.Project
            The project
        results : Union[RATapi.outputs.Results, RATapi.outputs.BayesResults]
            The calculation results.
        """
        if project is None or results is None:
            self.clear()
            return

        data = RATapi.events.PlotEventData()

        data.modelType = project.model
        data.reflectivity = results.reflectivity
        data.shiftedData = results.shiftedData
        data.sldProfiles = results.sldProfiles
        data.resampledLayers = results.resampledLayers
        data.dataPresent = RATapi.inputs.make_data_present(project)
        data.subRoughs = results.contrastParams.subRoughs
        data.resample = RATapi.inputs.make_resample(project)
        data.contrastNames = [contrast.name for contrast in project.contrasts]
        self.plot_event(data)

    def plot_event(self, data: Optional[RATapi.events.PlotEventData] = None):
        """Updates the ref and SLD plots from a provided or cached plot event

        Parameters
        ----------
        data : Optional[RATapi.events.PlotEventData]
            plot event data, cached data is used if none is provided
        """

        if data is not None:
            self.current_plot_data = data

        if self.current_plot_data is None:
            return

        show_legend = self.show_legend.isChecked() if self.current_plot_data.contrastNames else False
        RATapi.plotting.plot_ref_sld_helper(
            self.current_plot_data,
            self.figure,
            delay=False,
            linear_x=self.x_axis.currentText() == "Linear",
            q4=self.y_axis.currentText() == "Q^4",
            show_error_bar=self.show_error_bar.isChecked(),
            show_grid=self.show_grid.isChecked(),
            show_legend=show_legend,
        )
        self.figure.tight_layout(pad=1)
        self.canvas.draw()


class CornerPlotWidget(AbstractPlotWidget):
    """Widget for plotting corner plots."""


class HistPlotWidget(AbstractPlotWidget):
    """Widget for plotting Bayesian posterior panels."""


class ContourPlotWidget(AbstractPlotWidget):
    """Widget for plotting a contour plot of two parameters."""

    def __init__(self, parent):
        super().__init__(parent)
        self.layout().setStretch(1, 0)

    def make_control_layout(self):
        control_layout = QtWidgets.QVBoxLayout()

        self.x_param_box = QtWidgets.QComboBox(self)
        self.x_param_box.currentTextChanged.connect(lambda: self.draw_plot())
        self.x_param_box.setDisabled(True)

        self.y_param_box = QtWidgets.QComboBox(self)
        self.y_param_box.currentTextChanged.connect(lambda: self.draw_plot())
        self.y_param_box.setDisabled(True)

        self.smooth_checkbox = QtWidgets.QCheckBox(self)
        self.smooth_checkbox.setChecked(True)
        self.smooth_checkbox.checkStateChanged.connect(lambda: self.draw_plot())

        x_param_row = QtWidgets.QHBoxLayout()
        x_param_row.addWidget(QtWidgets.QLabel("x Parameter:"))
        x_param_row.addWidget(self.x_param_box)

        y_param_row = QtWidgets.QHBoxLayout()
        y_param_row.addWidget(QtWidgets.QLabel("y Parameter:"))
        y_param_row.addWidget(self.y_param_box)

        smooth_row = QtWidgets.QHBoxLayout()
        smooth_row.addWidget(QtWidgets.QLabel("Smooth contour:"))
        smooth_row.addWidget(self.smooth_checkbox)

        self.error_msg = QtWidgets.QLabel("Contour plots are only available\nfor Bayesian calculations.")

        control_layout.addLayout(x_param_row)
        control_layout.addLayout(y_param_row)
        control_layout.addLayout(smooth_row)
        control_layout.addStretch()
        control_layout.addWidget(self.error_msg)

        return control_layout

    def plot(self, _, results: Union[RATapi.outputs.Results, RATapi.outputs.BayesResults]):
        """Plot the contour for two parameters."""
        fit_params = results.fitNames

        old_x_param = self.x_param_box.currentText()
        old_y_param = self.y_param_box.currentText()
        self.x_param_box.clear()
        self.y_param_box.clear()

        if not isinstance(results, RATapi.outputs.BayesResults):
            self.current_plot_data = None
        else:
            self.current_plot_data = results

        if self.current_plot_data is None:
            self.x_param_box.setDisabled(True)
            self.y_param_box.setDisabled(True)
            self.error_msg.setVisible(True)
            return

        self.x_param_box.setDisabled(False)
        self.y_param_box.setDisabled(False)
        self.error_msg.setVisible(False)

        self.x_param_box.addItems([""] + fit_params)
        if old_x_param in fit_params:
            self.x_param_box.setCurrentText(old_x_param)
        self.y_param_box.addItems([""] + fit_params)
        if old_y_param in fit_params:
            self.y_param_box.setCurrentText(old_y_param)

        self.draw_plot()

    def draw_plot(self):
        self.clear()
        if self.current_plot_data is None:
            return

        x_param = self.x_param_box.currentText()
        y_param = self.y_param_box.currentText()
        smooth = self.smooth_checkbox.checkState() == QtCore.Qt.CheckState.Checked

        if x_param != "" and y_param != "":
            RATapi.plotting.plot_contour(self.current_plot_data, x_param, y_param, smooth, axes=self.figure.axes[0])
            self.canvas.draw()


class ChainPlotWidget(AbstractPlotWidget):
    """Widget for plotting a Bayesian chain panel."""
