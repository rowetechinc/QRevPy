from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
import matplotlib.cm as cm
import numpy as np
from datetime import datetime
import matplotlib.dates as mdates
from Classes.Measurement import Measurement
from MiscLibs.common_functions import convert_temperature
from matplotlib.ticker import MaxNLocator


class Qtmpl(FigureCanvas):
    """Initializes a QT5 figure canvas for matplotlib plots and contains the
    plotting functions used in QRev.

    Attributes
    ----------
    fig: Figure
        The figure containing all the plots, subplots, axes, etc.
    """

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        """Intializes the figure canvas and fig attribute.

        Parameters
        ----------
        parent: Object
            Parent of object class.
        width: float
            Width of figure in inches.
        height: float
            Height of figure in inches.
        dpi: float
            Screen resolution in dots per inch used to scale figure.
        """

        # Initialize figure
        self.fig = Figure(figsize=(width, height), dpi=dpi)

        # Configure FigureCanvas
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def contour_shiptrack(self, transect, units):
        """Generates the combination color contour and shiptrack plots in a single figure. Used in the main window.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData contain data to be plotted.
        units: dict
            Dictionary of unit conversions and labels.
        """

        # Setup grid space
        gs = gridspec.GridSpec(1, 4)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.05, bottom=0.2, right=0.98, top=0.85, wspace=0.1, hspace=0)

        # Generate color contour
        self.fig.axc = self.fig.add_subplot(gs[0, 0:3])
        self.color_contour(transect=transect, units=units)

        # Generate shiptrack
        self.fig.axst = self.fig.add_subplot(gs[0, 3])
        self.shiptrack_plot(transect=transect, units=units)

    def color_contour(self, transect, units):
        """Generates the color contour plot.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData contain data to be plotted.
        units: dict
            Dictionary of unit conversions and labels
        """

        x_plt, cell_plt, speed_plt, ensembles, depth = self.color_contour_data_prep(transect=transect,
                                                                                    data_type='Processed')
        # Determine limits for color map
        max_limit = 0
        min_limit = 0
        if np.sum(np.logical_not(np.isnan(speed_plt))) > 0:
            max_limit = np.percentile(speed_plt * units['V'], 99)

        # Create color map
        cmap = cm.get_cmap('viridis')
        cmap.set_under('white')

        # Generate color contour
        c = self.fig.axc.pcolor(x_plt, cell_plt * units['L'], speed_plt * units['V'], cmap=cmap, vmin=min_limit,
                                vmax=max_limit)

        # Add color bar and axis labels
        cb = self.fig.colorbar(c, pad=0.02)
        self.fig.axc.set_title(self.tr('Water Speed ') + units['label_V'])
        self.fig.axc.invert_yaxis()
        self.fig.axc.plot(ensembles, depth * units['L'], color='k')
        self.fig.axc.set_xlabel(self.tr('Ensembles'))
        self.fig.axc.set_ylabel(self.tr('Depth ') + units['label_L'])
        self.fig.axc.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
        self.fig.axc.set_ylim(top=0, bottom=np.ceil(np.nanmax(depth * units['L'])))
        if transect.start_edge == 'Right':
            self.fig.axc.invert_xaxis()

    @staticmethod
    def color_contour_data_prep(transect, data_type='Processed'):
        """Modifies the selected data from transect into arrays matching the meshgrid format for
        creating contour or color plots.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData containing data to be plotted
        data_type: str
            Specifies Processed or Filtered data type to be be plotted

        Returns
        -------
        x_plt: np.array
            Data in meshgrid format used for the contour x variable
        cell_plt: np.array
            Data in meshgrid format used for the contour y variable
        speed_plt: np.array
            Data in meshgrid format used to determine colors in plot
        ensembles: np.array
            Ensemble numbers used as the x variable to plot the cross section bottom
        depth: np.array
            Depth data used to plot the cross section bottom
        """
        in_transect_idx = transect.in_transect_idx

        # Get data from transect
        if data_type == 'Processed':
            water_u = transect.w_vel.u_processed_mps[:, in_transect_idx]
            water_v = transect.w_vel.v_processed_mps[:, in_transect_idx]
        else:
            water_u = transect.w_vel.u_mps[:, in_transect_idx]
            water_v = transect.w_vel.v_mps[:, in_transect_idx]

        depth_selected = getattr(transect.depths, transect.depths.selected)
        depth = depth_selected.depth_processed_m[in_transect_idx]
        cell_depth = depth_selected.depth_cell_depth_m[:, in_transect_idx]
        cell_size = depth_selected.depth_cell_size_m[:, in_transect_idx]
        ensembles = in_transect_idx

        # Prep water speed to use -999 instead of nans
        water_speed = np.sqrt(water_u ** 2 + water_v ** 2)
        speed = np.copy(water_speed)
        speed[np.isnan(speed)] = -999

        # Set x variable to ensembles
        x = np.tile(ensembles, (cell_size.shape[0], 1))
        n_ensembles = x.shape[1]

        # Prep data in x direction
        j = -1
        x_xpand = np.tile(np.nan, (cell_size.shape[0], 2 * cell_size.shape[1]))
        cell_depth_xpand = np.tile(np.nan, (cell_size.shape[0], 2 * cell_size.shape[1]))
        cell_size_xpand = np.tile(np.nan, (cell_size.shape[0], 2 * cell_size.shape[1]))
        speed_xpand = np.tile(np.nan, (cell_size.shape[0], 2 * cell_size.shape[1]))
        depth_xpand = np.array([np.nan] * (2 * cell_size.shape[1]))

        # Center ensembles in grid
        for n in range(n_ensembles):
            if n == 0:
                half_back = np.abs(0.5 * (x[:, n + 1] - x[:, n]))
                half_forward = half_back
            elif n == n_ensembles - 1:
                half_forward = np.abs(0.5 * (x[:, n] - x[:, n - 1]))
                half_back = half_forward
            else:
                half_back = np.abs(0.5 * (x[:, n] - x[:, n - 1]))
                half_forward = np.abs(0.5 * (x[:, n + 1] - x[:, n]))
            j += 1
            x_xpand[:, j] = x[:, n] - half_back
            cell_depth_xpand[:, j] = cell_depth[:, n]
            speed_xpand[:, j] = speed[:, n]
            cell_size_xpand[:, j] = cell_size[:, n]
            depth_xpand[j] = depth[n]
            j += 1
            x_xpand[:, j] = x[:, n] + half_forward
            cell_depth_xpand[:, j] = cell_depth[:, n]
            speed_xpand[:, j] = speed[:, n]
            cell_size_xpand[:, j] = cell_size[:, n]
            depth_xpand[j] = depth[n]

        # Create plotting mesh grid
        n_cells = x.shape[0]
        j = -1
        x_plt = np.tile(np.nan, (2 * cell_size.shape[0], 2 * cell_size.shape[1]))
        speed_plt = np.tile(np.nan, (2 * cell_size.shape[0], 2 * cell_size.shape[1]))
        cell_plt = np.tile(np.nan, (2 * cell_size.shape[0], 2 * cell_size.shape[1]))
        for n in range(n_cells):
            j += 1
            x_plt[j, :] = x_xpand[n, :]
            cell_plt[j, :] = cell_depth_xpand[n, :] - 0.5 * cell_size_xpand[n, :]
            speed_plt[j, :] = speed_xpand[n, :]
            j += 1
            x_plt[j, :] = x_xpand[n, :]
            cell_plt[j, :] = cell_depth_xpand[n, :] + 0.5 * cell_size_xpand[n, :]
            speed_plt[j, :] = speed_xpand[n, :]
        return x_plt, cell_plt, speed_plt, ensembles, depth

    def shiptrack_plot(self, transect, units):
        """Generates the shiptrack plot using all available references. Water vectors are plotted based on
        the selected reference.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData contain data to be plotted.
        units: dict
            Dictionary of unit conversions and labels
        """

        max_x_vtg = np.nan
        max_y_vtg = np.nan
        min_x_vtg = np.nan
        min_y_vtg = np.nan

        # Plot shiptrack based on bottom track
        ship_data_bt = transect.boat_vel.compute_boat_track(transect, ref='bt_vel')
        self.fig.axst.plot(ship_data_bt['track_x_m'] * units['L'], ship_data_bt['track_y_m'] * units['L'], color='r',
                           label='BT')
        ship_data = ship_data_bt
        max_x_bt = np.nanmax(ship_data_bt['track_x_m'])
        max_y_bt = np.nanmax(ship_data_bt['track_y_m'])
        min_x_bt = np.nanmin(ship_data_bt['track_x_m'])
        min_y_bt = np.nanmin(ship_data_bt['track_y_m'])

        # Plot shiptrack based on vtg if available
        if transect.boat_vel.vtg_vel is not None:
            ship_data_vtg = transect.boat_vel.compute_boat_track(transect, ref='vtg_vel')
            self.fig.axst.plot(ship_data_vtg['track_x_m'] * units['L'], ship_data_vtg['track_y_m'] * units['L'],
                               color='g', label='VTG')
            if transect.boat_vel.selected == 'vtg_vel':
                ship_data = ship_data_vtg

            max_x_vtg = np.nanmax(ship_data_vtg['track_x_m'])
            max_y_vtg = np.nanmax(ship_data_vtg['track_y_m'])
            min_x_vtg = np.nanmin(ship_data_vtg['track_x_m'])
            min_y_vtg = np.nanmin(ship_data_vtg['track_y_m'])

        # Plot shiptrack based on gga if available
        if transect.boat_vel.gga_vel is not None:
            ship_data_gga = transect.boat_vel.compute_boat_track(transect, ref='gga_vel')
            self.fig.axst.plot(ship_data_gga['track_x_m'] * units['L'], ship_data_gga['track_y_m'] * units['L'],
                               color='b', label='GGA')
            if transect.boat_vel.selected == 'gga_vel':
                ship_data = ship_data_gga

            max_x_gga = np.nanmax(ship_data_gga['track_x_m'])
            max_y_gga = np.nanmax(ship_data_gga['track_y_m'])
            min_x_gga = np.nanmin(ship_data_gga['track_x_m'])
            min_y_gga = np.nanmin(ship_data_gga['track_y_m'])

        # Customize axes
        self.fig.axst.set_xlabel(self.tr('Distance East ') + units['label_L'])
        self.fig.axst.set_ylabel(self.tr('Distance North ') + units['label_L'])
        self.fig.axst.xaxis.label.set_fontsize(10)
        self.fig.axst.yaxis.label.set_fontsize(10)
        self.fig.axst.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
        self.fig.axst.grid()
        self.fig.axst.axis('equal')
        for label in (self.fig.axst.get_xticklabels() + self.fig.axst.get_yticklabels()):
            label.set_fontsize(10)

        max_x = np.nanmax([max_x_bt, max_x_gga, max_x_vtg])
        min_x = np.nanmin([min_x_bt, min_x_gga, min_x_vtg])
        max_x = max_x + (max_x - min_x) * 0.1
        min_x = min_x - (max_x - min_x) * 0.1
        max_y = np.nanmax([max_y_bt, max_y_gga, max_y_vtg])
        min_y = np.nanmin([min_y_bt, min_y_gga, min_y_vtg])
        max_y = max_y + (max_y - min_y) * 0.1
        min_y = min_y - (max_y - min_y) * 0.1

        self.fig.axst.set_ylim(top=np.ceil(max_y * units['L']), bottom=np.ceil(min_y * units['L']))
        self.fig.axst.set_xlim(left=np.ceil(min_x * units['L']), right=np.ceil(max_x * units['L']))

        # Compute mean water velocity for each ensemble
        u = transect.w_vel.u_processed_mps
        v = transect.w_vel.v_processed_mps
        u_mean = np.nanmean(u, axis=0)
        v_mean = np.nanmean(v, axis=0)

        # Plot water vectors
        quiv_plt = self.fig.axst.quiver(ship_data['track_x_m'] * units['L'], ship_data['track_y_m'] * units['L'],
                                        u_mean * units['V'], v_mean * units['V'], units='dots', width=1, scale=0.6)
        # qk = axst.quiverkey(quiv_plt, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
        #                    coordinates='figure')

        self.fig.axst.legend(loc='best')

    def extrap_plot(self, meas):
        """Generates the extrapolation plot.

        Parameters
        ----------
        meas: Measurement
            Object of class Measurement
        """

        # Configure axis
        self.fig.ax = self.fig.add_subplot(111)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.2, bottom=0.15, right=0.98, top=0.98, wspace=0.1, hspace=0)

        # Plot median values with error bars
        self.extrap_plot_med(meas.extrap_fit.norm_data[-1])

        # Plot selected and automatic fits
        self.extrap_plot_fit(meas.extrap_fit.sel_fit[-1])

        # Customize axis
        self.fig.ax.set_xlabel(self.tr('Normalized Unit Q '))
        self.fig.ax.set_ylabel(self.tr('Normalized Z '))
        self.fig.ax.xaxis.label.set_fontsize(10)
        self.fig.ax.yaxis.label.set_fontsize(10)
        self.fig.ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
        self.fig.ax.grid()
        for label in (self.fig.ax.get_xticklabels() + self.fig.ax.get_yticklabels()):
            label.set_fontsize(10)
    #
    def extrap_plot_med(self, norm_data):
        """Plots median values and associated error bars.

        Parameters
        ----------
        norm_data: NormData
            Object of class NormData
        """

        # Plot all median values in red
        self.fig.ax.plot(norm_data.unit_normalized_med, norm_data.unit_normalized_z, 'rs', markerfacecolor='red')

        # Plot innerquartile range bars around medians in red
        for n in range(len(norm_data.unit_normalized_25)):
            self.fig.ax.plot([norm_data.unit_normalized_25[n], norm_data.unit_normalized_75[n]],
                             [norm_data.unit_normalized_z[n], norm_data.unit_normalized_z[n]],'r-')

        # Plot valid combined median values in black
        self.fig.ax.plot(norm_data.unit_normalized_med[norm_data.valid_data],
                         norm_data.unit_normalized_z[norm_data.valid_data], 'ks', markerfacecolor='black')

        # Plot innerquartile range bars around valid combined median values in black
        for idx in norm_data.valid_data:
            self.fig.ax.plot([norm_data.unit_normalized_25[idx], norm_data.unit_normalized_75[idx]],
                             [norm_data.unit_normalized_z[idx], norm_data.unit_normalized_z[idx]],'k-')

    def extrap_plot_fit(self, sel_fit, auto=True, selected=True):
        """Plots the automatic and/or selected fit.

        Parameters
        ----------
        sel_fit: SelectFit
            Object of class SelectFit
        auto: bool
            Determines if automatic fit is plotted
        selected: bool
            Determines if selected fit is plotted
        """

        if auto:
            self.fig.ax.plot(sel_fit.u_auto, sel_fit.z_auto, '-g', linewidth=3)

        if selected:
            self.fig.ax.plot(sel_fit.u, sel_fit.z, '-k', linewidth=2)

    def discharge_plot(self, meas, checked, units):
        """Generates the discharge plot.

        Parameters
        ----------
        meas: Measurement
            Object of class Measurement
        """

        # Configure axis
        self.fig.axq = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.2, bottom=0.15, right=0.98, top=0.98, wspace=0.1, hspace=0)

        for idx in checked:
            self.fig.axq.plot([datetime.fromtimestamp(meas.transects[idx].date_time.start_serial_time),
                               datetime.fromtimestamp(meas.transects[idx].date_time.end_serial_time)],
                              [meas.discharge[idx].total * units['Q'], meas.discharge[idx].total * units['Q']],'k-')

        # Customize axis
        timeFmt = mdates.DateFormatter('%H:%M:%S')
        self.fig.axq.xaxis.set_major_formatter(timeFmt)
        self.fig.axq.set_xlabel(self.tr('Time '))
        self.fig.axq.set_ylabel(self.tr('Discharge ') + units['label_Q'])
        self.fig.axq.xaxis.label.set_fontsize(10)
        self.fig.axq.yaxis.label.set_fontsize(10)
        self.fig.axq.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
        # self.fig.axq.xaxis.set_major_locator(MaxNLocator(4))
        self.fig.axq.grid()

    def heading_plot(self, qrev):
        """Generates the heading plot.

        Parameters
        ----------
        meas: Measurement
            Object of class Measurement
        """


        # Configure axis
        self.fig.axh = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.1, bottom=0.15, right=0.98, top=0.98, wspace=0.1, hspace=0)
        self.fig.axh.set_xlabel(self.tr('Ensembles (left to right) '))
        self.fig.axh.set_ylabel(self.tr('Heading (deg)'))
        self.fig.axh.xaxis.label.set_fontsize(10)
        self.fig.axh.yaxis.label.set_fontsize(10)
        self.fig.axh.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
        checked = qrev.checked_transects_idx
        meas = qrev.meas
        for row in range(len(checked)):
            if qrev.table_compass_pr.item(row, 0).checkState() == QtCore.Qt.Checked:
                if qrev.cb_adcp_compass.isChecked():
                    # Plot ADCP heading
                    heading = np.copy(meas.transects[checked[row]].sensors.heading_deg.internal.data)
                    if meas.transects[checked[row]].start_edge == 'Right':
                        np.flip(heading)
                    self.fig.axh.plot(heading, 'r-')

                if qrev.cb_ext_compass.isChecked():
                    # Plot External Heading
                    heading = np.copy(meas.transects[checked[row]].sensors.heading_deg.external.data)
                    if meas.transects[checked[row]].start_edge == 'Right':
                        np.flip(heading)
                    self.fig.axh.plot(heading, 'b-')

                if qrev.cb_mag_field.isChecked():
                    # Plot magnetic field change
                    self.fig.axm = self.fig.axh.twinx()
                    self.fig.axm.set_ylabel(self.tr('Magnetic Change (%)'))
                    self.fig.axm.yaxis.label.set_fontsize(10)
                    self.fig.axm.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
                    mag_chng = np.copy(meas.transects[checked[row]].sensors.heading_deg.internal.mag_error)
                    if meas.transects[checked[row]].start_edge == 'Right':
                        np.flip(mag_chng)
                    self.fig.axm.plot(mag_chng, 'k-')

    def pr_plot(self, qrev):
        """Generates the pitch and roll plot.

        Parameters
        ----------
        meas: Measurement
            Object of class Measurement
        """


        # Configure axis
        self.fig.axh = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.1, bottom=0.15, right=0.98, top=0.98, wspace=0.1, hspace=0)
        self.fig.axh.set_xlabel(self.tr('Ensembles (left to right) '))
        self.fig.axh.set_ylabel(self.tr('Pitch or Roll (deg)'))
        self.fig.axh.xaxis.label.set_fontsize(10)
        self.fig.axh.yaxis.label.set_fontsize(10)
        self.fig.axh.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
        checked = qrev.checked_transects_idx
        meas = qrev.meas
        for row in range(len(checked)):
            if qrev.table_compass_pr.item(row, 0).checkState() == QtCore.Qt.Checked:
                if qrev.cb_pitch.isChecked():
                    # Plot pitch
                    pitch = np.copy(meas.transects[checked[row]].sensors.pitch_deg.internal.data)
                    if meas.transects[checked[row]].start_edge == 'Right':
                        np.flip(pitch)
                    self.fig.axh.plot(pitch, 'r-')

                if qrev.cb_roll.isChecked():
                    # Plot roll
                    roll = np.copy(meas.transects[checked[row]].sensors.roll_deg.internal.data)
                    if meas.transects[checked[row]].start_edge == 'Right':
                        np.flip(roll)
                    self.fig.axh.plot(roll, 'b-')

    def temperature_plot(self, qrev):
        """Generates the temperature plot.

        Parameters
        ----------
        meas: Measurement
            Object of class Measurement
        """

        # Configure axis
        self.fig.axt = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.1, bottom=0.15, right=0.98, top=0.98, wspace=0.1, hspace=0)
        temp, serial_time = Measurement.compute_time_series(qrev.meas, 'Temperature')

        time_stamp = []
        for t in serial_time:
            time_stamp.append(datetime.fromtimestamp(t))

        y_label = qrev.tr('Degrees C')
        if qrev.rb_f.isChecked():
            temp = convert_temperature(temp_in=temp, units_in='C', units_out='F')
            y_label = qrev.tr('Degrees F')

        self.fig.axt.plot(time_stamp, temp, 'b.')

        # Customize axis
        timeFmt = mdates.DateFormatter('%H:%M:%S')
        self.fig.axt.xaxis.set_major_formatter(timeFmt)
        self.fig.axt.set_xlabel(qrev.tr('Time '))
        self.fig.axt.set_ylabel(y_label)
        self.fig.axt.xaxis.label.set_fontsize(12)
        self.fig.axt.yaxis.label.set_fontsize(12)
        self.fig.axt.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
        self.fig.axt.set_ylim([np.nanmax(temp) + 2, np.nanmin(temp) - 2])
        # self.fig.axq.xaxis.set_major_locator(MaxNLocator(4))
        self.fig.axt.grid()

