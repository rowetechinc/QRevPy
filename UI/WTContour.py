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
        self.hover_connection = None

    def create(self, transect, units, invalid_data=None, n_ensembles=None, edge_start=None, max_limit=0):
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

        if edge_start is None:
            x_plt, cell_plt, speed_plt, ensembles, depth = self.color_contour_data_prep(transect=transect,
                                                                                        data_type='Processed',
                                                                                        invalid_data=invalid_data,
                                                                                        n_ensembles = n_ensembles,
                                                                                       edge_start = edge_start)
        else:
            x_plt, cell_plt, speed_plt, ensembles, depth = self.color_contour_data_prep(transect=transect,
                                                                                        data_type='Raw',
                                                                                        invalid_data=invalid_data,
                                                                                        n_ensembles=n_ensembles,
                                                                                        edge_start=edge_start)
        self.x_plt = x_plt + 1
        self.cell_plt = cell_plt * self.units['L']
        self.speed_plt = speed_plt * self.units['V']
        # Determine limits for color map

        min_limit = 0
        if max_limit == 0:
            if np.sum(speed_plt[speed_plt > -900]) > 0:
                max_limit = np.percentile(speed_plt[speed_plt > -900] * units['V'], 99)
            else:
                max_limit = 1

        # Create color map
        cmap = cm.get_cmap('viridis')
        cmap.set_under('white')

        # Generate color contour
        c = self.fig.ax.pcolormesh(self.x_plt, self.cell_plt, self.speed_plt, cmap=cmap, vmin=min_limit,
                                vmax=max_limit)

        # Add color bar and axis labels
        cb = self.fig.colorbar(c, pad=0.02)
        cb.ax.set_ylabel(self.canvas.tr('Water Speed ') + units['label_V'])
        cb.ax.yaxis.label.set_fontsize(12)
        cb.ax.tick_params(labelsize=12)
        # self.fig.ax.set_title(self.canvas.tr('Water Speed ') + units['label_V'])
        self.fig.ax.invert_yaxis()
        self.fig.ax.plot(ensembles+1, depth * units['L'], color='k')
        if transect.w_vel.sl_cutoff_m is not None:
            depth_obj = getattr(transect.depths, transect.depths.selected)
            last_valid_cell = np.nansum(transect.w_vel.cells_above_sl, axis=0) - 1
            last_depth_cell_size= depth_obj.depth_cell_size_m[last_valid_cell,
                                                              np.arange(depth_obj.depth_cell_size_m.shape[1])]
            self.fig.ax.plot(ensembles+1,
                             (transect.w_vel.sl_cutoff_m + (last_depth_cell_size * 0.5))* units['L'],
                             color='r', linewidth=0.5)
            # Plot upper bound of measured depth cells
            self.fig.ax.plot(ensembles+1,
                             (depth_obj.depth_cell_depth_m[0,:]
                              - (depth_obj.depth_cell_size_m[0, :] * 0.5)) * units['L'],
                             color='r', linewidth=0.5)
        self.fig.ax.set_xlabel(self.canvas.tr('Ensembles'))
        self.fig.ax.set_ylabel(self.canvas.tr('Depth ') + units['label_L'])
        self.fig.ax.xaxis.label.set_fontsize(12)
        self.fig.ax.yaxis.label.set_fontsize(12)
        self.fig.ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
        self.fig.ax.set_ylim(top=0, bottom=np.ceil(np.nanmax(depth * units['L'])))
        self.fig.ax.set_xlim(left=ensembles[0] - len(ensembles) * 0.02, right=ensembles[-1] + len(ensembles) * 0.02)
        if transect.start_edge == 'Right':
            self.fig.ax.invert_xaxis()
            self.fig.ax.set_xlim(right=ensembles[0] - len(ensembles) * 0.02, left=ensembles[-1] + len(ensembles) * 0.02)

        # Initialize annotation for data cursor
        self.annot = self.fig.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                          bbox=dict(boxstyle="round", fc="w"),
                                          arrowprops=dict(arrowstyle="->"))

        self.annot.set_visible(False)

        self.canvas.draw()

        return max_limit

    @staticmethod
    def color_contour_data_prep(transect, data_type='Processed', invalid_data=None, n_ensembles=None, edge_start=None):
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
        if n_ensembles is None:
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
        else:
            n_ensembles = int(n_ensembles)
            if edge_start:
                if data_type == 'Processed':
                    water_u = transect.w_vel.u_processed_mps[:, :n_ensembles]
                    water_v = transect.w_vel.v_processed_mps[:, :n_ensembles]
                else:
                    water_u = transect.w_vel.u_mps[:, :n_ensembles]
                    water_v = transect.w_vel.v_mps[:, :n_ensembles]

                depth_selected = getattr(transect.depths, transect.depths.selected)
                depth = depth_selected.depth_processed_m[:n_ensembles]
                cell_depth = depth_selected.depth_cell_depth_m[:, :n_ensembles]
                cell_size = depth_selected.depth_cell_size_m[:, :n_ensembles]
                ensembles = in_transect_idx[:n_ensembles]
                if invalid_data is not None:
                    invalid_data = invalid_data[:, :n_ensembles]
            else:
                if data_type == 'Processed':
                    water_u = transect.w_vel.u_processed_mps[:, -n_ensembles:]
                    water_v = transect.w_vel.v_processed_mps[:, -n_ensembles:]
                else:
                    water_u = transect.w_vel.u_mps[:, -n_ensembles:]
                    water_v = transect.w_vel.v_mps[:, -n_ensembles:]

                depth_selected = getattr(transect.depths, transect.depths.selected)
                depth = depth_selected.depth_processed_m[-n_ensembles:]
                cell_depth = depth_selected.depth_cell_depth_m[:, -n_ensembles:]
                cell_size = depth_selected.depth_cell_size_m[:, -n_ensembles:]
                ensembles = in_transect_idx[-n_ensembles:]
                if invalid_data is not None:
                    invalid_data = invalid_data[:, -n_ensembles:]

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
        cell_plt[np.isnan(cell_plt)] = 0
        speed_plt[np.isnan(speed_plt)] = -999
        x_plt[np.isnan(x_plt)] == 0
        return x_plt, cell_plt, speed_plt, ensembles, depth

    def hover(self, event):
        vis = self.annot.get_visible()
        if event.inaxes == self.fig.ax:
            cont_fig = False
            if self.fig is not None:
                cont_fig, ind_fig = self.fig.contains(event)

            if cont_fig and self.fig.get_visible():
                # col_idx = (int(round(event.xdata)) - int(round(self.fig.ax.viewLim.x0))) * 2
                col_idx = (int(round(event.xdata)) * 2) - 1
                vel = None
                for n, cell in enumerate(self.cell_plt[:, col_idx]):
                    if event.ydata < cell:
                        vel = self.speed_plt[n, col_idx]
                        break

                self.update_annot(event.xdata, event.ydata, vel)
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            else:
                if vis:
                    self.annot.set_visible(False)
                    self.canvas.draw_idle()

    def set_hover_connection(self, setting):

        if setting and self.hover_connection is None:
            # self.hover_connection = self.canvas.mpl_connect("motion_notify_event", self.hover)
            self.hover_connection = self.canvas.mpl_connect('button_press_event', self.hover)
        elif not setting:
            self.canvas.mpl_disconnect(self.hover_connection)
            self.hover_connection = None

    def update_annot(self, x, y, v):

        plt_ref = self.fig
        # pos = plt_ref.get_offsets()[ind["ind"][0]]
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
        if v is not None and v > -999:
            text = 'x: {:.2f}, y: {:.2f}, \n v: {:.1f}'.format(int(round(x)), y, v)
        else:
            text = 'x: {:.2f}, y: {:.2f}'.format(int(round(x)), y)
        self.annot.set_text(text)