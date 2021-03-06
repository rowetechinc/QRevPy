import numpy as np


class ExtrapPlot(object):
    """Generates graphics of extrapolation.

    Attributes
    ----------
    canvas: MplCanvas
        Object of MplCanvas
    fig: Object
        Figure object of the canvas
    meas: Measurement
        Object of class Measurement
    checked: list
        List of transect indices of transects used to compute discharge
    hover_connection: int
        Index to data cursor connection
    annot: Annotation
        Annotation object for data cursor
    """

    def __init__(self, canvas):
        """Initialize object using the specified canvas.

        Parameters
        ----------
        canvas: MplCanvas
            Object of MplCanvas
        """

        # Initialize attributes
        self.canvas = canvas
        self.fig = canvas.fig
        self.meas = None
        self.checked = None
        self.hover_connection = None
        self.annot = None

    def create(self, meas, checked, idx=-1, data_type='Discharge',
               cb_data=True, cb_surface=False,
               cb_trans_medians=False, cb_trans_fit=False,
               cb_meas_medians=True, cb_meas_fit=True, auto=False):
        """Creates figure for extrapolation plot and calls associated methods to added data to the axes.

        Parameters
        ----------
        meas: Measurement
            Object of class Measurement
        checked: list
            List of indices of transects used to compute discharge
        idx: int
            Index of data to plot
        data_type: str
            Type of data (Discharge or Velocity)
        cb_data: bool
            Plot depth cell data (True or False)
        cb_surface: bool
            Highlight surface cell data (True or False)
        cb_trans_medians: bool
            Plot medians of transects (True or False)
        cb_trans_fit: bool
            Plot extrapolation fit for each transect (True or False)
        cb_meas_medians: bool
            Plot medians for entire measurement (True or False)
        cb_meas_fit: bool
            Plot extrapolation fit for entire measurement (True or False)
        auto: bool
            Indicator that the auto fit should be shown in addition to the selected fit.
        """

        # Initialize variables
        self.meas = meas
        self.checked = checked
        extrap_fit = meas.extrap_fit

        # Clear the plot
        self.fig.clear()

        # Configure axis
        self.fig.ax = self.fig.add_subplot(111)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.13, bottom=0.1, right=0.98, top=0.98, wspace=0.1, hspace=0)

        # If valid data exist create graph
        if np.any(np.logical_not(np.isnan(extrap_fit.norm_data[-1].unit_normalized))):

            # Show all normalized data
            if cb_data:
                self.extrap_plot_data(extrap_fit.norm_data[idx])

            # Highlight surface cells
            if cb_surface:
                self.extrap_plot_surface(extrap_fit.norm_data[idx])

            # Show fit for individual transect(s)
            if cb_trans_fit:
                if idx == len(extrap_fit.norm_data) - 1:
                    self.extrap_plot_fit(extrap_fit.sel_fit[0:-1])
                else:
                    self.extrap_plot_fit(extrap_fit.sel_fit[idx], idx)

            # Show median for individual transect(s)
            if cb_trans_medians:
                if idx == len(extrap_fit.norm_data) - 1:
                    self.extrap_plot_med(extrap_fit.norm_data[0:-1])
                else:
                    self.extrap_plot_med(extrap_fit.norm_data[idx], idx)

            # Show median values with error bars for measurement
            if cb_meas_medians:
                self.extrap_plot_med(extrap_fit.norm_data[-1], -1)

            # Show measurement fit
            if cb_meas_fit:
                self.extrap_plot_fit(extrap_fit.sel_fit[-1], -1, auto)

            # Configure axes
            if data_type == 'Discharge':
                self.fig.ax.set_xlabel(self.canvas.tr('Normalized Unit Q '))
            else:
                self.fig.ax.set_xlabel(self.canvas.tr('Normalized Velocity'))
            self.fig.ax.set_ylabel(self.canvas.tr('Normalized Z '))
            self.fig.ax.xaxis.label.set_fontsize(10)
            self.fig.ax.yaxis.label.set_fontsize(10)
            self.fig.ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
            self.fig.ax.grid()
            for label in (self.fig.ax.get_xticklabels() + self.fig.ax.get_yticklabels()):
                label.set_fontsize(10)

            # Scale axes
            if np.any(np.logical_not(np.isnan(extrap_fit.norm_data[idx].unit_normalized))):
                min_avg = np.nanmin(extrap_fit.norm_data[idx].unit_normalized_25[extrap_fit.norm_data[idx].valid_data])
                max_avg = np.nanmax(extrap_fit.norm_data[idx].unit_normalized_75[extrap_fit.norm_data[idx].valid_data])
            else:
                min_avg = np.nan
                max_avg = np.nan

            if min_avg > 0 and max_avg > 0:
                min_avg = 0
                lower = 0
            elif np.isnan(min_avg):
                lower = 0
            else:
                lower = min_avg * 1.2

            if max_avg < 0 and min_avg < 0:
                upper = 0
            elif np.isnan(max_avg):
                upper = 0
            else:
                upper = max_avg * 1.2

            self.fig.ax.set_ylim(top=1, bottom=0)
            self.fig.ax.set_xlim(left=lower, right=upper)

            # Initialize annotation for data cursor
            self.annot = self.fig.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                              bbox=dict(boxstyle="round", fc="w"),
                                              arrowprops=dict(arrowstyle="->"))

            self.annot.set_visible(False)

            self.canvas.draw()

    def extrap_plot_med(self, norm_data, idx=None):
        """Plots median values and associated error bars.

        Parameters
        ----------
        norm_data: list or NormData
            List of or single object of class NormData
        idx: int
            Index to data to be plotted
        """

        # If norm_data is a list is contains data from multiple transects
        if type(norm_data) is list:

            # Plot all transects
            for idx in self.checked:

                # All median values in red
                self.fig.ax.plot(norm_data[idx].unit_normalized_med, norm_data[idx].unit_normalized_z, 'rs',
                                 markerfacecolor='red', linestyle='None')

                # All error bars in red
                for n in range(len(norm_data[idx].unit_normalized_25)):
                    self.fig.ax.plot([norm_data[idx].unit_normalized_25[n], norm_data[idx].unit_normalized_75[n]],
                                     [norm_data[idx].unit_normalized_z[n], norm_data[idx].unit_normalized_z[n]],
                                     '-r')

                # Color valid transect data by start bank
                if self.meas.transects[idx].start_edge == 'Left':
                    line_color = '#ff00ff'
                else:
                    line_color = 'b'

                # Valid median values
                self.fig.ax.plot(norm_data[idx].unit_normalized_med[norm_data[idx].valid_data],
                                 norm_data[idx].unit_normalized_z[norm_data[idx].valid_data],
                                 marker='s', color=line_color, markerfacecolor=line_color,
                                 linestyle='None')

                # Valid error bars
                for n in norm_data[idx].valid_data:
                    self.fig.ax.plot([norm_data[idx].unit_normalized_25[n], norm_data[idx].unit_normalized_75[n]],
                                     [norm_data[idx].unit_normalized_z[n], norm_data[idx].unit_normalized_z[n]],
                                     color=line_color)

        # Data for only 1 transect of the composite measurement
        else:

            # If composite measurement the color is black otherwise use start bank
            if idx == -1:
                line_color = 'k'
            elif self.meas.transects[idx].start_edge == 'Left':
                line_color = '#ff00ff'
            else:
                line_color = 'b'

            # All median values in red
            self.fig.ax.plot(norm_data.unit_normalized_med, norm_data.unit_normalized_z, 'rs',
                             markerfacecolor='red', linestyle='None')

            # All error bars in red
            for n in range(len(norm_data.unit_normalized_25)):
                self.fig.ax.plot([norm_data.unit_normalized_25[n], norm_data.unit_normalized_75[n]],
                                 [norm_data.unit_normalized_z[n], norm_data.unit_normalized_z[n]],
                                 'r-')

            # Valid median values
            self.fig.ax.plot(norm_data.unit_normalized_med[norm_data.valid_data],
                             norm_data.unit_normalized_z[norm_data.valid_data],
                             marker='s', color=line_color, markerfacecolor=line_color,
                             linestyle='None')

            # Valid error bars
            for idx in norm_data.valid_data:
                self.fig.ax.plot([norm_data.unit_normalized_25[idx], norm_data.unit_normalized_75[idx]],
                                 [norm_data.unit_normalized_z[idx], norm_data.unit_normalized_z[idx]],
                                 color=line_color)

    def extrap_plot_fit(self, sel_fit, idx=None, auto=False):
        """Plots the automatic and/or selected fit.

        Parameters
        ----------
        sel_fit: list or SelectFit
            List of or single object of class SelectFit
        idx: int
            Index of data to be plotted
        auto: bool
            Indicator that the auto fit should be shown in addition to the selected fit.
        """

        # If sel_fit is a list plot data from all checked transects
        if type(sel_fit) is list:
            for idx in self.checked:
                if self.meas.transects[idx].start_edge == 'Left':
                    line_color = '#ff00ff'
                else:
                    line_color = 'b'

                self.fig.ax.plot(sel_fit[idx].u, sel_fit[idx].z, color=line_color, linewidth=2)

        # If sel_fit is a single data set
        else:
            # If the data set is a composite for the measurement plot in black otherwise use start bank
            if idx == -1:
                line_color = 'k'
            elif self.meas.transects[idx].start_edge == 'Left':
                line_color = '#ff00ff'
            else:
                line_color = 'b'

            # Used by main tab to show both Auto and Selected.
            if auto:
                self.fig.ax.plot(sel_fit.u_auto, sel_fit.z_auto, '-g', linewidth=3)
            self.fig.ax.plot(sel_fit.u, sel_fit.z, color=line_color, linewidth=2)

    def extrap_plot_data(self, norm_data):
        """Plot normalized data for each depth cell. These data will be either for a single transect or for the
        composite for the whole measurement.

        Parameters
        ----------
        norm_data: NormData
            Object of class NormData

        """

        self.fig.ax.plot(norm_data.unit_normalized, 1 - norm_data.cell_depth_normalized, marker='o',
                         color='#cecece', markerfacecolor='#cecece', linestyle='None', markersize=2)

    def extrap_plot_surface(self, norm_data):
        """Highlights the depth cell data representing the topmost depth cell. These data will be either for a
        single transect or for the composite for the whole measurement.

        Parameters
        ----------
        norm_data: NormData
            Object of class NormData
        """

        # Indentify indices for topmost depth cell
        surface_idx = np.argmax(np.logical_not(np.isnan(norm_data.unit_normalized)), 0)
        idx = (surface_idx, range(len(surface_idx)))

        # Plot data
        self.fig.ax.plot(norm_data.unit_normalized[idx], 1 - norm_data.cell_depth_normalized[idx], marker='o',
                         markerfacecolor='g', linestyle='None', markersize=2)

    def hover(self, event):
        """Determines if the user has selected a location with data and makes
        annotation visible and calls method to update the text of the annotation. If the
        location is not valid the existing annotation is hidden.

        Parameters
        ----------
        event: MouseEvent
            Triggered when mouse button is pressed.
        """

        # Set annotation to visible
        vis = self.annot.get_visible()

        # Determine if mouse location references a data point in the plot and update the annotation.
        if event.inaxes == self.fig.ax:
            cont_fig = False
            if self.fig is not None:
                cont_fig, ind_fig = self.fig.contains(event)

            if cont_fig and self.fig.get_visible():
                self.update_annot(event.xdata, event.ydata)
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            else:
                if vis:
                    self.annot.set_visible(False)
                    self.canvas.draw_idle()

    def set_hover_connection(self, setting):
        """Turns the connection to the mouse event on or off.

        Parameters
        ----------
        setting: bool
            Boolean to specify whether the connection for the mouse event is active or not.
        """

        if setting and self.hover_connection is None:
            self.hover_connection = self.canvas.mpl_connect('button_press_event', self.hover)
        elif not setting:
            self.canvas.mpl_disconnect(self.hover_connection)
            self.hover_connection = None
            self.annot.set_visible(False)
            self.canvas.draw_idle()

    def update_annot(self, x, y):
        """Updates the location and text and makes visible the previously initialized and hidden annotation.

        Parameters
        ----------
        x: int
            x coordinate for annotation
        y: int
            y coordinate for annotation
        """

        plt_ref = self.fig
        pos = [x, y]
        # Shift annotation box left or right depending on which half of the axis the pos x is located and the
        # direction of x increasing.
        if plt_ref.ax.viewLim.intervalx[0] < plt_ref.ax.viewLim.intervalx[1]:
            if pos[0] < (plt_ref.ax.viewLim.intervalx[0] + plt_ref.ax.viewLim.intervalx[1]) / 2:
                self.annot._x = -20
            else:
                self.annot._x = -80
        else:
            if pos[0] < (plt_ref.ax.viewLim.intervalx[0] + plt_ref.ax.viewLim.intervalx[1]) / 2:
                self.annot._x = -80
            else:
                self.annot._x = -20

        # Shift annotation box up or down depending on which half of the axis the pos y is located and the
        # direction of y increasing.
        if plt_ref.ax.viewLim.intervaly[0] < plt_ref.ax.viewLim.intervaly[1]:
            if pos[1] > (plt_ref.ax.viewLim.intervaly[0] + plt_ref.ax.viewLim.intervaly[1]) / 2:
                self.annot._y = -40
            else:
                self.annot._y = 20
        else:
            if pos[1] > (plt_ref.ax.viewLim.intervaly[0] + plt_ref.ax.viewLim.intervaly[1]) / 2:
                self.annot._y = 20
            else:
                self.annot._y = -40
        self.annot.xy = pos

        text = 'x: {:.2f}, y: {:.2f}'.format(x, y)

        self.annot.set_text(text)
