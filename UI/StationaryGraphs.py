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
    mb: list
        List of plot objects
    stud: list
        List of plot objects
    hover_connection: int
        Index to data cursor connection
    annot_mb: Annotation
        Annotation object for moving-bed time series data cursor
    annot_stud: Annotation
        Annotation object for upstream/downstream shiptrack data cursor
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
        self.hover_connection = None
        self.annot_mb = None
        self.annot_stud = None
        self.mb = None
        self.stud = None

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

        # Configure moving-bed time series graph
        self.fig.axmb = self.fig.add_subplot(gs[0, 0])
        self.fig.axmb.set_xlabel(self.canvas.tr('Ensembles'))
        self.fig.axmb.set_ylabel(self.canvas.tr('Moving-bed speed' + units['label_V']))
        self.fig.axmb.grid()
        self.fig.axmb.xaxis.label.set_fontsize(12)
        self.fig.axmb.yaxis.label.set_fontsize(12)
        self.fig.axmb.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)

        # Mark invalid data
        valid_data = mb_test.transect.boat_vel.bt_vel.valid_data[0, mb_test.transect.in_transect_idx]
        if np.any(valid_data):
            invalid_data = np.logical_not(valid_data)
            ensembles = np.arange(1, len(valid_data) + 1)
            self.mb = self.fig.axmb.plot(ensembles, mb_test.stationary_mb_vel * units['V'], 'b-')
            self.mb.append(self.fig.axmb.plot(ensembles[invalid_data],
                                              mb_test.stationary_mb_vel[invalid_data] * units['V'], 'ro')[0])

            # Generate upstream/cross stream shiptrack
            self.fig.axstud = self.fig.add_subplot(gs[0, 1])
            self.fig.axstud.set_xlabel(self.canvas.tr('Distance cross stream' + units['label_L']))
            self.fig.axstud.set_ylabel(self.canvas.tr('Distance upstream' + units['label_L']))
            self.fig.axstud.grid()
            self.fig.axstud.xaxis.label.set_fontsize(12)
            self.fig.axstud.yaxis.label.set_fontsize(12)
            self.fig.axstud.axis('equal')
            self.fig.axstud.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)

            self.stud = self.fig.axstud.plot(mb_test.stationary_cs_track * units['L'],
                                             mb_test.stationary_us_track * units['L'], 'r-')

            # Initialize annotation for data cursor
            self.annot_mb = self.fig.axmb.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                                   bbox=dict(boxstyle="round", fc="w"),
                                                   arrowprops=dict(arrowstyle="->"))

            self.annot_mb.set_visible(False)

            # Initialize annotation for data cursor
            self.annot_stud = self.fig.axstud.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                                       bbox=dict(boxstyle="round", fc="w"),
                                                       arrowprops=dict(arrowstyle="->"))

            self.annot_stud.set_visible(False)

            self.canvas.draw()

    def change(self):
        """Function to all call to change, but there is nothing to change for this class. Mirrors BoatSpeed class
        to allow interchangable use.
        """
        pass

    @staticmethod
    def update_annot(ind, plt_ref, annot):
        """Updates the location and text and makes visible the previously initialized and hidden annotation.

        Parameters
        ----------
        ind: dict
            Contains data selected.
        plt_ref: Line2D
            Reference containing plotted data
        annot: Annotation
            Annotation associated with figure clicked
        """

        pos = plt_ref._xy[ind["ind"][0]]

        # Shift annotation box left or right depending on which half of the axis the pos x is located and the
        # direction of x increasing.
        if plt_ref.axes.viewLim.intervalx[0] < plt_ref.axes.viewLim.intervalx[1]:
            if pos[0] < (plt_ref.axes.viewLim.intervalx[0] + plt_ref.axes.viewLim.intervalx[1]) / 2:
                annot._x = -20
            else:
                annot._x = -80
        else:
            if pos[0] < (plt_ref.axes.viewLim.intervalx[0] + plt_ref.axes.viewLim.intervalx[1]) / 2:
                annot._x = -80
            else:
                annot._x = -20

        # Shift annotation box up or down depending on which half of the axis the pos y is located and the
        # direction of y increasing.
        if plt_ref.axes.viewLim.intervaly[0] < plt_ref.axes.viewLim.intervaly[1]:
            if pos[1] > (plt_ref.axes.viewLim.intervaly[0] + plt_ref.axes.viewLim.intervaly[1]) / 2:
                annot._y = -40
            else:
                annot._y = 20
        else:
            if pos[1] > (plt_ref.axes.viewLim.intervaly[0] + plt_ref.axes.viewLim.intervaly[1]) / 2:
                annot._y = 20
            else:
                annot._y = -40

        # Format and display text
        annot.xy = pos
        text = 'x: {:.2f}, y: {:.2f}'.format(pos[0], pos[1])
        annot.set_text(text)

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
        vis_mb = self.annot_mb.get_visible()
        vis_stud = self.annot_stud.get_visible()

        # Determine if mouse location references a data point in the plot and update the annotation.
        if event.inaxes == self.fig.axmb:
            cont_mb = False
            ind_mb = None
            if self.mb is not None:
                cont_mb, ind_mb = self.mb[0].contains(event)
            if cont_mb and self.mb[0].get_visible():
                self.update_annot(ind_mb, self.mb[0], self.annot_mb)
                self.annot_mb.set_visible(True)
                self.canvas.draw_idle()
            else:
                if vis_mb:
                    self.annot_mb.set_visible(False)
                    self.canvas.draw_idle()
        elif event.inaxes == self.fig.axstud:
            cont_stud = False
            ind_stud = None
            if self.stud is not None:
                cont_stud, ind_stud = self.stud[0].contains(event)
            if cont_stud and self.stud[0].get_visible():
                self.update_annot(ind_stud, self.stud[0], self.annot_stud)
                self.annot_stud.set_visible(True)
                self.canvas.draw_idle()
            else:
                # If the cursor location is not associated with the plotted data hide the annotation.
                if vis_stud:
                    self.annot_stud.set_visible(False)
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
