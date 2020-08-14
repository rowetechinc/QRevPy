import numpy as np
from datetime import datetime
import matplotlib.dates as mdates
from MiscLibs.common_functions import convert_temperature


class TemperatureTS(object):
    """Class to generate a time series graph of the ADCP temperature.

    Attributes
    ----------
    canvas: MplCanvas
        Object of MplCanvas a FigureCanvas
    tp: list
        Reference to time series plot
    hover_connection: bool
        Switch to allow user to use the data cursor
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
        self.tp = None
        self.hover_connection = None
        self.annot = None

    def create(self, meas, rb_f):
        """Creates the figure on the canvas.

        Parameters
        ----------
        meas: Measurement
            Object of class Measurement
        rb_f: Widget
            Radio button control for F or C units
        """

        # Clear the plot
        self.fig.clear()

        # Configure axis
        self.fig.ax = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.1, bottom=0.15, right=0.98, top=0.98, wspace=0.1, hspace=0)
        temp, serial_time = meas.compute_time_series(meas, 'Temperature')

        # Create list from time stamps
        time_stamp = []
        for t in serial_time:
            time_stamp.append(datetime.utcfromtimestamp(t))

        # Set label to display correct units
        y_label = self.canvas.tr('Degrees C')
        if rb_f.isChecked():
            temp = convert_temperature(temp_in=temp, units_in='C', units_out='F')
            y_label = self.canvas.tr('Degrees F')

        # Plot data
        self.tp = self.fig.ax.plot(time_stamp, temp, 'b.')

        # Customize axis
        time_fmt = mdates.DateFormatter('%H:%M:%S')
        self.fig.ax.xaxis.set_major_formatter(time_fmt)
        self.fig.ax.set_xlabel(self.canvas.tr('Time '))
        self.fig.ax.set_ylabel(y_label)
        self.fig.ax.xaxis.label.set_fontsize(12)
        self.fig.ax.yaxis.label.set_fontsize(12)
        self.fig.ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
        self.fig.ax.set_ylim([np.nanmin(temp) - 2, np.nanmax(temp) + 2])
        self.fig.ax.grid()

        # Initialize annotation for data cursor
        self.annot = self.fig.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                          bbox=dict(boxstyle="round", fc="w"),
                                          arrowprops=dict(arrowstyle="->"))

        self.annot.set_visible(False)

        self.canvas.draw()

    def update_annot(self, ind, plt_ref):
        """Updates the location and text and makes visible the previously initialized and hidden annotation.

        Parameters
        ----------
        ind: dict
            Contains data selected.
        plt_ref: Line2D
            Reference containing plotted data
        """

        # Get selected data coordinates
        pos = plt_ref._xy[ind["ind"][0]]

        # Shift annotation box left or right depending on which half of the axis the pos x is located and the
        # direction of x increasing.
        if plt_ref.axes.viewLim.intervalx[0] < plt_ref.axes.viewLim.intervalx[1]:
            if pos[0] < (plt_ref.axes.viewLim.intervalx[0] + plt_ref.axes.viewLim.intervalx[1]) / 2:
                self.annot._x = -20
            else:
                self.annot._x = -80
        else:
            if pos[0] < (plt_ref.axes.viewLim.intervalx[0] + plt_ref.axes.viewLim.intervalx[1]) / 2:
                self.annot._x = -80
            else:
                self.annot._x = -20

        # Shift annotation box up or down depending on which half of the axis the pos y is located and the
        # direction of y increasing.
        if plt_ref.axes.viewLim.intervaly[0] < plt_ref.axes.viewLim.intervaly[1]:
            if pos[1] > (plt_ref.axes.viewLim.intervaly[0] + plt_ref.axes.viewLim.intervaly[1]) / 2:
                self.annot._y = -40
            else:
                self.annot._y = 20
        else:
            if pos[1] > (plt_ref.axes.viewLim.intervaly[0] + plt_ref.axes.viewLim.intervaly[1]) / 2:
                self.annot._y = 20
            else:
                self.annot._y = -40
        self.annot.xy = pos

        # Format and display text
        text = 'x: {}, y: {:.2f}'.format(plt_ref._xorig[ind["ind"][0]].strftime("%H:%M:%S"), pos[1])
        self.annot.set_text(text)

    def hover(self, event):
        """Determines if the user has selected a location with temperature data and makes
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
            cont = False
            ind = None
            if self.tp is not None:
                cont, ind = self.tp[0].contains(event)

            if cont and self.tp[0].get_visible():
                self.update_annot(ind, self.tp[0])
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            else:
                # If the cursor location is not associated with the plotted data hide the annotation.
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
            # self.hover_connection = self.canvas.mpl_connect("motion_notify_event", self.hover)
            self.hover_connection = self.canvas.mpl_connect('button_press_event', self.hover)
        elif not setting:
            self.canvas.mpl_disconnect(self.hover_connection)
            self.hover_connection = None
            self.annot.set_visible(False)
            self.canvas.draw_idle()
