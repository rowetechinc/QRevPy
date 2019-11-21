import numpy as np
from PyQt5 import QtCore


class HeadingTS(object):
    """Class to generate at time series of heading data.

    Attributes
    ----------
    canvas: MplCanvas
        Object of MplCanvas a FigureCanvas
    internal: list
        Reference to internal compass time series plot
    external: list
        Reference to internal compass time series plot
    merror: list
        Reference to magnetic error time series plot
    row_index: list
        List of rows from the table that are plotted
    hover_connection: bool
        Switch to allow user to use the data cursor
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
        self.internal = None
        self.external = None
        self.merror = None
        self.row_index = []
        self.hover_connection = None

    def create(self, meas, checked, tbl, cb_internal, cb_external, cb_merror):

        # Clear the plot
        self.fig.clear()
        self.row_index = []

        # Configure axis
        self.fig.axh = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.1, bottom=0.15, right=0.95, top=0.98, wspace=0.1, hspace=0)
        self.fig.axh.set_xlabel(self.canvas.tr('Ensembles (left to right) '))
        self.fig.axh.set_ylabel(self.canvas.tr('Heading (deg)'))
        self.fig.axh.xaxis.label.set_fontsize(10)
        self.fig.axh.yaxis.label.set_fontsize(10)
        self.fig.axh.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)

        if cb_merror.isChecked():
            # Plot magnetic field change
            self.fig.axm = self.fig.axh.twinx()
            self.fig.axm.set_ylabel(self.canvas.tr('Magnetic Change (%)'))
            self.fig.axm.yaxis.label.set_fontsize(10)
            self.fig.axm.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)

        self.internal = []
        self.external = []
        self.merror = []
        for row in range(len(checked)):
            if tbl.item(row, 0).checkState() == QtCore.Qt.Checked:
                self.row_index.append(row)
                if cb_internal.isChecked():
                    # Plot ADCP heading
                    heading = np.copy(meas.transects[checked[row]].sensors.heading_deg.internal.data)
                    if meas.transects[checked[row]].start_edge == 'Right':
                        heading = np.flip(heading)
                    self.internal.append(self.fig.axh.plot(heading, 'r-')[0])
                else:
                    self.internal = None

                if cb_external.isChecked():
                    # Plot External Heading
                    heading = np.copy(meas.transects[checked[row]].sensors.heading_deg.external.data)
                    if meas.transects[checked[row]].start_edge == 'Right':
                        heading = np.flip(heading)
                    self.external.append(self.fig.axh.plot(heading, 'b-')[0])
                else:
                    self.external = None

                if cb_merror.isChecked():
                    # Plot magnetic field change
                    mag_chng = np.copy(meas.transects[checked[row]].sensors.heading_deg.internal.mag_error)
                    if meas.transects[checked[row]].start_edge == 'Right':
                        mag_chng = np.flip(mag_chng)
                    self.merror.append(self.fig.axm.plot(mag_chng, 'k-')[0])
                else:
                    self.merror = None

        if cb_merror.isChecked():
            self.annot2 = self.fig.axm.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                               bbox=dict(boxstyle="round", fc="w"),
                                               arrowprops=dict(arrowstyle="->"))

            self.annot2.set_visible(False)

        # Initialize annotation for data cursor
        self.annot = self.fig.axh.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                          bbox=dict(boxstyle="round", fc="w"),
                                          arrowprops=dict(arrowstyle="->"))

        self.annot.set_visible(False)

        self.canvas.draw()

    def update_annot(self, annot, ind, plt_ref, row):
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

        annot.xy = pos

        # Format and display text
        text = 'row: {:.0f}, x: {:.2f}, y: {:.2f}'.format(row, pos[0], pos[1])
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
        vis = self.annot.get_visible()

        cont = False
        # Determine if mouse location references a data point in the plot and update the annotation.
        if event.inaxes == self.fig.axh or event.inaxes == self.fig.axm:
            if self.internal is not None:
                for n, item in enumerate(self.internal):
                    cont, ind = item.contains(event)
                    if cont:
                        break
            if not cont and self.external is not None:
                for n, item in enumerate(self.external):
                    cont, ind = item.contains(event)
                    if cont:
                        break
            if cont:
                self.update_annot(annot=self.annot, ind=ind, plt_ref=item, row=self.row_index[n]+1)
                self.annot.set_visible(True)
                self.canvas.draw_idle()
                if self.merror is not None:
                    self.annot2.set_visible(False)

            else:
                self.annot.set_visible(False)
                if self.merror is not None:
                    for n, item in enumerate(self.merror):
                        cont, ind = item.contains(event)
                        if cont:
                            break
                if cont:
                    self.update_annot(annot=self.annot2, ind=ind, plt_ref=item, row=self.row_index[n]+1)
                    self.annot2.set_visible(True)
                    self.canvas.draw_idle()
                else:
                    self.annot2.set_visible(False)
        else:
            # If the cursor location is not associated with the plotted data hide the annotation.
            if vis:
                self.annot.set_visible(False)
                if self.merror is not None:
                    self.annot2.set_visible(False)
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