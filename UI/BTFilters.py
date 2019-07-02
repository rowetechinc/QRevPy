import numpy as np
import copy


class BTFilters(object):
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
    other: object
        Axis of figure for other filters
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
        self.other = None

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

        if selected == 'beam':
            # Plot beams
            # Determine number of beams for each ensemble
            bt_temp = copy.deepcopy(transect.boat_vel.bt_vel)
            bt_temp.filter_beam(4)
            valid_4beam = bt_temp.valid_data[5, :].astype(int)
            beam_data = np.copy(valid_4beam).astype(int)
            beam_data[valid_4beam == 1] = 4
            beam_data[valid_4beam == 0] = 3
            beam_data[np.logical_not(transect.boat_vel.bt_vel.valid_data[1, :])] = 0

            # Plot all data
            self.beam = self.fig.ax.plot(ensembles, beam_data, 'b.')

            # Circle invalid data
            invalid_beam = np.logical_not(transect.boat_vel.bt_vel.valid_data[5, :])
            self.beam.append(self.fig.ax.plot(ensembles[invalid_beam],
                                              beam_data[invalid_beam], 'ro', markerfacecolor='none')[0])

            # Format axis
            self.fig.ax.set_ylim(top=4.5, bottom=-0.5)
            self.fig.ax.set_ylabel(self.canvas.tr('Number of Beams'))

        elif selected == 'error':
            # Plot error velocity
            max_y = np.nanmax(transect.boat_vel.bt_vel.d_mps) * 1.1
            min_y = np.nanmin(transect.boat_vel.bt_vel.d_mps) * 1.1
            invalid_error_vel = np.logical_not(transect.boat_vel.bt_vel.valid_data[2, :])
            self.error = self.fig.ax.plot(ensembles, transect.boat_vel.bt_vel.d_mps * units['V'], 'b.')
            self.error.append(self.fig.ax.plot(ensembles[invalid_error_vel],
                                               transect.boat_vel.bt_vel.d_mps[invalid_error_vel] * units['V'],
                                               'ro', markerfacecolor='none')[0])
            self.fig.ax.set_ylim(top=max_y * units['V'], bottom=min_y * units['V'])
            self.fig.ax.set_ylabel(self.canvas.tr('Error Velocity' + self.units['label_V']))

        elif selected == 'vert':
            # Plot vertical velocity
            max_y = np.nanmax(transect.boat_vel.bt_vel.w_mps) * 1.1
            min_y = np.nanmin(transect.boat_vel.bt_vel.w_mps) * 1.1
            invalid_vert_vel = np.logical_not(transect.boat_vel.bt_vel.valid_data[3, :])
            self.vert = self.fig.ax.plot(ensembles, transect.boat_vel.bt_vel.w_mps * units['V'], 'b.')
            self.vert.append(self.fig.ax.plot(ensembles[invalid_vert_vel],
                                              transect.boat_vel.bt_vel.w_mps[invalid_vert_vel] * units['V'],
                                              'ro', markerfacecolor='none')[0])
            self.fig.ax.set_ylim(top=max_y * units['V'], bottom=min_y * units['V'])
            self.fig.ax.set_ylabel(self.canvas.tr('Vert. Velocity' + self.units['label_V']))

        elif selected == 'other':
            # Plot smooth
            speed = np.sqrt(transect.boat_vel.bt_vel.u_mps ** 2
                            + transect.boat_vel.bt_vel.v_mps ** 2)
            invalid_other_vel = np.logical_not(transect.boat_vel.bt_vel.valid_data[4, :])
            if transect.boat_vel.bt_vel.smooth_filter == 'On':
                self.other = self.fig.ax.plot(ensembles,
                                              transect.boat_vel.bt_vel.smooth_lower_limit * self.units['V'],
                                              color='#d5dce6')
                self.other.append(self.fig.ax.plot(ensembles,
                                                   transect.boat_vel.bt_vel.smooth_upper_limit * self.units['V'],
                                                   color='#d5dce6')[0])
                self.other.append(self.fig.ax.fill_between(ensembles,
                                                           transect.boat_vel.bt_vel.smooth_lower_limit
                                                           * self.units['V'],
                                                           transect.boat_vel.bt_vel.smooth_upper_limit
                                                           * self.units['V'],
                                                           facecolor='#d5dce6'))

                self.other.append(self.fig.ax.plot(ensembles, speed * units['V'], 'r-')[0])
                self.other.append(self.fig.ax.plot(ensembles,
                                                   transect.boat_vel.bt_vel.smooth_speed * self.units['V'])[0])
                self.other.append(self.fig.ax.plot(ensembles[invalid_other_vel],
                                                   speed[invalid_other_vel] * units['V'],
                                                   'ko', linestyle='')[0])
            else:
                self.other = self.fig.ax.plot(ensembles, speed * units['V'], 'r-')

            self.fig.ax.set_ylabel(self.canvas.tr('Speed' + self.units['label_V']))
        self.fig.ax.set_xlim(left=-1 * ensembles[-1] * 0.02, right=ensembles[-1] * 1.02)

        self.canvas.draw()
