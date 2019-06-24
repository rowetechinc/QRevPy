import numpy as np
import matplotlib.gridspec as gridspec


class StationaryGraphs(object):
    """Class to generate two time series plots (moving-bed velocity and shiptrack based on upstream/downstream
    movement) used to evaluate stationary moving-bed tests.

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

        self.canvas = canvas
        self.fig = canvas.fig

    def create(self, mb_test, units):
        """Generates a moving-bed time series and upstream/downstream bottom track plot from stationary moving-bed
        test data.

        Parameters
        ----------
        mb_test: MovingBedTest
            Object of MovingBedTest contain data to be plotted.
        units: dict
            Dictionary of unit conversions and labels.
        """

        # Clear the plot
        self.fig.clear()

        # Setup grid space
        gs = gridspec.GridSpec(1, 2)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.1, bottom=0.1, right=0.98, top=0.85, wspace=0.2, hspace=0)

        # Generate color contour
        self.fig.axmb = self.fig.add_subplot(gs[0, 0])
        self.fig.axmb.set_xlabel(self.canvas.tr('Ensembles'))
        self.fig.axmb.set_ylabel(self.canvas.tr('Moving-bed speed' + units['label_V']))
        self.fig.axmb.grid()
        self.fig.axmb.xaxis.label.set_fontsize(12)
        self.fig.axmb.yaxis.label.set_fontsize(12)
        self.fig.axmb.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)

        valid_data = mb_test.transect.boat_vel.bt_vel.valid_data[0, mb_test.transect.in_transect_idx]
        invalid_data = np.logical_not(valid_data)
        ensembles = np.arange(1, len(valid_data) + 1)
        self.fig.axmb.plot(ensembles, mb_test.stationary_mb_vel * units['V'], 'b-')
        self.fig.axmb.plot(ensembles[invalid_data], mb_test.stationary_mb_vel[invalid_data] * units['V'], 'ro')

        # Generate upstream/cross stream shiptrack
        self.fig.axstud = self.fig.add_subplot(gs[0, 1])
        self.fig.axstud.set_xlabel(self.canvas.tr('Distance cross stream' + units['label_L']))
        self.fig.axstud.set_ylabel(self.canvas.tr('Distance upstream' + units['label_L']))
        self.fig.axstud.grid()
        self.fig.axstud.xaxis.label.set_fontsize(12)
        self.fig.axstud.yaxis.label.set_fontsize(12)
        self.fig.axstud.axis('equal')
        self.fig.axstud.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)

        self.fig.axstud.plot(mb_test.stationary_cs_track * units['L'], mb_test.stationary_us_track * units['L'], 'r-')

        self.canvas.draw()

    def change(self):
        """Function to all call to change, but there is nothing to change for this class. Mirrors BoatSpeed class
        to allow interchangable use.
        """
        pass