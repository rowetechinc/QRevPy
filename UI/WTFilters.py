import numpy as np
import copy


class WTFilters(object):
    """Class to generate time series plots of the selected filter data.

    Attributes
    ----------
    canvas: MplCanvas
        Object of MplCanvas a FigureCanvas
    fig: Object
        Figure object of the canvas
    units: dict
        Dictionary of units conversions
    beam: object
        Axis of figure for number of beams
    error: object
        Axis of figure for error velocity
    vert: object
        Axis of figure for vertical velocity
    speed: object
        Axis of figure for speed time series
    snr: object
        Axis of figure for snr filters
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
        self.beam = None
        self.error = None
        self.vert = None
        self.speed = None
        self.snr = None

    def create(self, transect, units, selected):
        """Create the axes and lines for the figure.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData containing boat speeds to be plotted
        units: dict
            Dictionary of units conversions
        selected: str
            String identifying the type of plot
        """

        # Assign and save parameters
        self.units = units

        # Clear the plot
        self.fig.clear()

        # Configure axis
        self.fig.ax = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.07, bottom=0.2, right=0.99, top=0.98, wspace=0.1, hspace=0)
        self.fig.ax.set_xlabel(self.canvas.tr('Ensembles'))
        self.fig.ax.grid()
        self.fig.ax.xaxis.label.set_fontsize(12)
        self.fig.ax.yaxis.label.set_fontsize(12)
        self.fig.ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)

        ensembles = np.arange(1, len(transect.boat_vel.bt_vel.u_mps) + 1)
        ensembles = np.tile(ensembles, (transect.w_vel.valid_data[0, :, :].shape[0], 1))

        cas = transect.w_vel.cells_above_sl

        if selected == 'beam':
            # Plot beams
            # Determine number of beams for each ensemble
            wt_temp = copy.deepcopy(transect.w_vel)
            wt_temp.filter_beam(4)
            valid_4beam = wt_temp.valid_data[5, :, :].astype(int)
            beam_data = np.copy(valid_4beam).astype(int)
            beam_data[valid_4beam == 1] = 4
            beam_data[wt_temp.valid_data[6, :, :]] = 4
            beam_data[valid_4beam == 0] = 3
            beam_data[np.logical_not(transect.w_vel.valid_data[1, :, :])] = -999

            # Plot all data
            self.beam = self.fig.ax.plot(ensembles, beam_data, 'b.')

            # Circle invalid data
            invalid_beam = np.logical_and(np.logical_not(transect.w_vel.valid_data[5, :, :]), cas)
            self.beam.append(self.fig.ax.plot(ensembles[invalid_beam],
                                              beam_data[invalid_beam], 'ro', markerfacecolor='none')[0])

            # Format axis
            self.fig.ax.set_ylim(top=4.5, bottom=-0.5)
            self.fig.ax.set_ylabel(self.canvas.tr('Number of Beams'))

        elif selected == 'error':
            # Plot error velocity
            max_y = np.nanmax(transect.w_vel.d_mps[cas]) * 1.1
            min_y = np.nanmin(transect.w_vel.d_mps[cas]) * 1.1
            invalid_error_vel = np.logical_and(np.logical_not(transect.w_vel.valid_data[2, :, :]), cas)
            self.error = self.fig.ax.plot(ensembles[cas], transect.w_vel.d_mps[cas] * units['V'], 'b.')
            self.error.append(self.fig.ax.plot(ensembles[invalid_error_vel],
                                               transect.w_vel.d_mps[invalid_error_vel] * units['V'],
                                               'ro', markerfacecolor='none')[0])
            self.fig.ax.set_ylim(top=max_y * units['V'], bottom=min_y * units['V'])
            self.fig.ax.set_ylabel(self.canvas.tr('Error Velocity' + self.units['label_V']))

        elif selected == 'vert':
            # Plot vertical velocity
            max_y = np.nanmax(transect.w_vel.w_mps[cas]) * 1.1
            min_y = np.nanmin(transect.w_vel.w_mps[cas]) * 1.1
            invalid_vert_vel = np.logical_and(np.logical_not(transect.w_vel.valid_data[3, :, :]), cas)
            self.vert = self.fig.ax.plot(ensembles[cas], transect.w_vel.w_mps[cas] * units['V'], 'b.')
            self.vert.append(self.fig.ax.plot(ensembles[invalid_vert_vel],
                                              transect.w_vel.w_mps[invalid_vert_vel] * units['V'],
                                              'ro', markerfacecolor='none')[0])
            self.fig.ax.set_ylim(top=max_y * units['V'], bottom=min_y * units['V'])
            self.fig.ax.set_ylabel(self.canvas.tr('Vert. Velocity' + self.units['label_V']))

        elif selected == 'snr':
            # Plot snr
            max_y = np.nanmax(transect.w_vel.snr_rng) * 1.1
            min_y = np.nanmin(transect.w_vel.snr_rng) * 1.1
            invalid_snr = np.logical_not(transect.w_vel.valid_data[7, 0, :])
            self.snr = self.fig.ax.plot(ensembles[0, :], transect.w_vel.snr_rng, 'b.')
            self.snr.append(self.fig.ax.plot(ensembles[0, invalid_snr],
                                             transect.w_vel.snr_rng[invalid_snr],
                                             'ro', markerfacecolor='none')[0])
            self.fig.ax.set_ylim(top=max_y , bottom=min_y)
            self.fig.ax.set_ylabel(self.canvas.tr('SNR (dB)'))

        elif selected == 'speed':
            # Plot speed
            speed = np.nanmean(np.sqrt(transect.w_vel.u_mps ** 2
                            + transect.w_vel.v_mps ** 2), 0)
            max_y = np.nanmax(speed) * 1.1
            min_y = np.nanmin(speed) * 1.1
            invalid_wt = np.logical_and(np.logical_not(transect.w_vel.valid_data), cas)

            self.speed = self.fig.ax.plot(ensembles[0, :],
                                          speed * self.units['V'],
                                          'b')
            self.speed.append(self.fig.ax.plot(ensembles[0, np.any(invalid_wt[1, :, :], 0)],
                                               speed[np.any(invalid_wt[1, :, :], 0)] * units['V'],
                                               'k', linestyle='', marker='$O$')[0])
            self.speed.append(self.fig.ax.plot(ensembles[0, np.any(invalid_wt[2, :, :], 0)],
                                               speed[np.any(invalid_wt[2, :, :], 0)] * units['V'],
                                               'k', linestyle='', marker='$E$')[0])
            self.speed.append(self.fig.ax.plot(ensembles[0, np.any(invalid_wt[3, :, :], 0)],
                                               speed[np.any(invalid_wt[3, :, :], 0)] * units['V'],
                                               'k', linestyle='', marker='$V$')[0])
            self.speed.append(self.fig.ax.plot(ensembles[0, np.any(invalid_wt[5, :, :], 0)],
                                               speed[np.any(invalid_wt[5, :, :], 0)] * units['V'],
                                               'k', linestyle='', marker='$B$')[0])
            self.speed.append(self.fig.ax.plot(ensembles[0, np.any(invalid_wt[7, :, :], 0)],
                                               speed[np.any(invalid_wt[7, :, :], 0)] * units['V'],
                                               'k', linestyle='', marker='$R$')[0])

            self.fig.ax.set_ylabel(self.canvas.tr('Speed' + self.units['label_V']))
            self.fig.ax.set_ylim(top=max_y * units['V'], bottom=min_y * units['V'])

        self.fig.ax.set_xlim(left=-1 * ensembles[0, -1] * 0.02, right=ensembles[0, -1] * 1.02)

        if transect.start_edge == 'Right':
            self.fig.ax.invert_xaxis()
            self.fig.ax.set_xlim(right=-1 * ensembles[0, -1] * 0.02, left=ensembles[0, -1] * 1.02)

        self.canvas.draw()
