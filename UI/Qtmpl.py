from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
import matplotlib.cm as cm
import numpy as np


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
        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.05, bottom=0.2, right=0.98, top=0.85, wspace=0.1, hspace=0)

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
            max_limit = np.percentile(speed_plt, 95)

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

        # Plot all available shiptracks
        ship_data_bt = transect.boat_vel.compute_boat_track(transect, ref='bt_vel')
        self.fig.axst.plot(ship_data_bt['track_x_m'] * units['L'], ship_data_bt['track_y_m'] * units['L'], color='r',
                           label='BT')
        ship_data = ship_data_bt

        if transect.boat_vel.vtg_vel is not None:
            ship_data_vtg = transect.boat_vel.compute_boat_track(transect, ref='vtg_vel')
            self.fig.axst.plot(ship_data_vtg['track_x_m'] * units['L'], ship_data_vtg['track_y_m'] * units['L'],
                               color='g', label='VTG')
            if transect.boat_vel.selected == 'vtg_vel':
                ship_data = ship_data_vtg

        if transect.boat_vel.gga_vel is not None:
            ship_data_gga = transect.boat_vel.compute_boat_track(transect, ref='gga_vel')
            self.fig.axst.plot(ship_data_gga['track_x_m'] * units['L'], ship_data_gga['track_y_m'] * units['L'],
                               color='b', label='GGA')
            if transect.boat_vel.selected == 'gga_vel':
                ship_data = ship_data_gga

        self.fig.axst.set_xlabel(self.tr('Distance East ') + units['label_L'])
        self.fig.axst.set_ylabel(self.tr('Distance North ') + units['label_L'])
        self.fig.axst.xaxis.label.set_fontsize(10)
        self.fig.axst.yaxis.label.set_fontsize(10)
        self.fig.axst.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
        self.fig.axst.grid()
        for label in (self.fig.axst.get_xticklabels() + self.fig.axst.get_yticklabels()):
            label.set_fontsize(10)

        # Compute mean water velocity for each ensemble
        u = transect.w_vel.u_processed_mps
        v = transect.w_vel.v_processed_mps
        u_mean = np.nanmean(u, axis=0)
        v_mean = np.nanmean(v, axis=0)

        quiv_plt = self.fig.axst.quiver(ship_data['track_x_m'] * units['L'], ship_data['track_y_m'] * units['L'],
                                        u_mean * units['V'], v_mean * units['V'], units='dots', width=2, scale=.02)
        # qk = axst.quiverkey(quiv_plt, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
        #                    coordinates='figure')

        self.fig.axst.legend(loc='best')


