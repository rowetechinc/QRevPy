from PyQt5 import QtCore
import numpy as np
import matplotlib.cm as cm


class WTContour(object):
    """Class to generate the color contour plot of water speed data.

    Attributes
    ----------
    canvas: MplCanvas
            Object of MplCanvas a FigureCanvas
    fig: Object
        Figure object of the canvas
    units: dict
        Dictionary of units conversions
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
        self.units = None

    def create(self, transect, units, invalid_data=None):
        """Create the axes and lines for the figure.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData containing boat speeds to be plotted
        units: dict
            Dictionary of units conversions
        invalid_data: np.array(bool)
            Array indicating which depth cells contain invalid data
        """

        # Assign and save parameters
        self.units = units

        # Clear the plot
        self.fig.clear()

        # Configure axis
        self.fig.ax = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.08, bottom=0.2, right=1, top=0.97, wspace=0.1, hspace=0)

        x_plt, cell_plt, speed_plt, ensembles, depth = self.color_contour_data_prep(transect=transect,
                                                                                    data_type='Processed',
                                                                                    invalid_data=invalid_data)
        # Determine limits for color map
        max_limit = 0
        min_limit = 0
        if np.sum(np.logical_not(np.isnan(speed_plt))) > 0:
            max_limit = np.percentile(speed_plt * units['V'], 99)

        # Create color map
        cmap = cm.get_cmap('viridis')
        cmap.set_under('white')

        # Generate color contour
        c = self.fig.ax.pcolor(x_plt, cell_plt * units['L'], speed_plt * units['V'], cmap=cmap, vmin=min_limit,
                                vmax=max_limit)

        # Add color bar and axis labels
        cb = self.fig.colorbar(c, pad=0.02)
        cb.ax.set_ylabel(self.canvas.tr('Water Speed ') + units['label_V'])
        # self.fig.ax.set_title(self.canvas.tr('Water Speed ') + units['label_V'])
        self.fig.ax.invert_yaxis()
        self.fig.ax.plot(ensembles, depth * units['L'], color='k')
        self.fig.ax.set_xlabel(self.canvas.tr('Ensembles'))
        self.fig.ax.set_ylabel(self.canvas.tr('Depth ') + units['label_L'])
        self.fig.ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
        self.fig.ax.set_ylim(top=0, bottom=np.ceil(np.nanmax(depth * units['L'])))
        self.fig.ax.set_xlim(left=-1 * ensembles[-1] * 0.02, right=ensembles[-1] * 1.02)
        if transect.start_edge == 'Right':
            self.fig.ax.invert_xaxis()
            self.fig.ax.set_xlim(right=-1 * ensembles[-1] * 0.02, left=ensembles[-1] * 1.02)

        self.canvas.draw()
    @staticmethod
    def color_contour_data_prep(transect, data_type='Processed', invalid_data=None):
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
        if invalid_data is not None:
            speed[invalid_data] = -999

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
