from PyQt5 import QtCore
import numpy as np


class CrossSection(object):
    """Class to generate final cross sections using the user settings.
    What cross sections are plotted are controlled by the user through checkboxes.

    Attributes
    ----------
    canvas: MplCanvas
        Object of MplCanvas a FigureCanvas
    fig: Object
        Figure object of the canvas
    units: dict
        Dictionary of units conversions
    cb_beam_cs: QCheckBox
        Checkbox to plot cross section based on 4 beam average
    cb_vert_cs: QCheckBox
        Checkbox to plot cross section based on vertical beam
    cb_ds_cs: QCheckBox
        Checkbox to plot cross section based on depth sounder
    cb_final_cs: QCheckBox
        Checkbox to plot final cross section based on user selections
    beam_cs: list
        Plot reference for 4 beam average cross section
    vb_cs: list
        Plot reference for vertical beam cross section
    ds_cs: list
        Plot reference for depth sounder cross section
    final_cs: list
        Plot reference for final cross section
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
        self.cb_beam_cs = None
        self.cb_vert_cs = None
        self.cb_ds_cs = None
        self.cb_final_cs = None
        self.beam_cs = None
        self.vb_cs = None
        self.ds_cs = None
        self.final_cs = None
        self.hover_connection = None

    def create(self, transect, units,
               cb_beam_cs=None,
               cb_vert_cs=None,
               cb_ds_cs=None,
               cb_final_cs=None):

        """Create the axes and lines for the figure.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData containing boat speeds to be plotted
        units: dict
            Dictionary of units conversions
        cb_beam_cs: QCheckBox
            Checkbox to plot cross section based on 4 beam average
        cb_vert_cs: QCheckBox
            Checkbox to plot cross section based on vertical beam
        cb_ds_cs: QCheckBox
            Checkbox to plot cross section based on depth sounder
        cb_final_cs: QCheckBox
            Checkbox to plot final cross section based on user selections
        """

        # Assign and save parameters
        self.cb_beam_cs = cb_beam_cs
        self.cb_vert_cs = cb_vert_cs
        self.cb_ds_cs = cb_ds_cs
        self.cb_final_cs = cb_final_cs

        # Clear the plot
        self.fig.clear()

        # Configure axis
        self.fig.ax = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.08, bottom=0.2, right=0.98, top=0.98, wspace=0.1, hspace=0)
        self.fig.ax.set_xlabel(self.canvas.tr('Length' + units['label_L']))
        self.fig.ax.set_ylabel(self.canvas.tr('Depth' + units['label_L']))
        self.fig.ax.grid()
        self.fig.ax.xaxis.label.set_fontsize(12)
        self.fig.ax.yaxis.label.set_fontsize(12)
        self.fig.ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)

        # Initialize max trackers
        max_vb = np.nan
        max_ds = np.nan

        # Compute x axis data
        boat_track = transect.boat_vel.compute_boat_track(transect=transect)
        x = boat_track['distance_m']
        if not np.alltrue(np.isnan(boat_track['track_x_m'])):
            depth_selected = getattr(transect.depths, transect.depths.selected)
            beam_depths = depth_selected.depth_processed_m

            # Plot Final
            self.final_cs = self.fig.ax.plot(x * units['L'],
                                             beam_depths * units['L'],
                                             'k-')
            max_final = np.nanmax(beam_depths)

            # Plot 4 beam average
            beam_depths = transect.depths.bt_depths.depth_processed_m
            self.beam_cs = self.fig.ax.plot(x * units['L'],
                                            beam_depths * units['L'],
                                            'r-')
            max_beam = np.nanmax(beam_depths)

            # Plot vertical beam
            if transect.depths.vb_depths is not None:
                beam_depths = transect.depths.vb_depths.depth_processed_m
                self.vb_cs = self.fig.ax.plot(x * units['L'],
                                              beam_depths * units['L'],
                                              color='#aa00ff',
                                              linestyle='-')
                max_vb = np.nanmax(beam_depths)

            # Plot depth sounder
            if transect.depths.ds_depths is not None:
                beam_depths = transect.depths.ds_depths.depth_processed_m
                self.ds_cs = self.fig.ax.plot(x * units['L'],
                                              beam_depths * units['L'],
                                              color='#00aaff',
                                              linestyle='-')
                max_ds = np.nanmax(beam_depths)

            # Based on checkbox control make cross sections visible or not
            if cb_beam_cs.checkState() == QtCore.Qt.Checked:
                for item in self.beam_cs:
                    item.set_visible(True)
            else:
                for item in self.beam_cs:
                    item.set_visible(False)

            if cb_vert_cs.isEnabled():
                if cb_vert_cs.checkState() == QtCore.Qt.Checked:
                    for item in self.vb_cs:
                        item.set_visible(True)
                elif self.vb_cs is not None:
                    for item in self.vb_cs:
                        item.set_visible(False)

            if cb_ds_cs.isEnabled():
                if cb_ds_cs.checkState() == QtCore.Qt.Checked:
                    for item in self.ds_cs:
                        item.set_visible(True)
                elif self.ds_cs is not None:
                    for item in self.ds_cs:
                        item.set_visible(False)

            # Set axis limits
            max_y = np.nanmax([max_beam, max_vb, max_ds, max_final]) * 1.1
            self.fig.ax.invert_yaxis()
            self.fig.ax.set_ylim(bottom=np.ceil(max_y * units['L']), top=0)
            self.fig.ax.set_xlim(left=-1 * x[-1] * 0.02 * units['L'], right=x[-1] * 1.02 * units['L'])

            if transect.start_edge == 'Right':
                self.fig.ax.invert_xaxis()
                self.fig.ax.set_xlim(right=-1 * x[-1] * 0.02 * units['L'], left=x[-1] * 1.02 * units['L'])

            # Initialize annotation for data cursor
            self.annot = self.fig.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                              bbox=dict(boxstyle="round", fc="w"),
                                              arrowprops=dict(arrowstyle="->"))

            self.annot.set_visible(False)

            self.canvas.draw()

    def change(self):
        """Changes the visibility of the available beams based on user input via checkboxes.
        """

        # Set visibility of beams based on user input
        if self.cb_beam_cs.checkState() == QtCore.Qt.Checked:
            for item in self.beam_cs:
                item.set_visible(True)
        else:
            for item in self.beam_cs:
                item.set_visible(False)

        if self.cb_vert_cs.isEnabled():
            if self.cb_vert_cs.checkState() == QtCore.Qt.Checked:
                for item in self.vb_cs:
                    item.set_visible(True)
            else:
                for item in self.vb_cs:
                    item.set_visible(False)

        if self.cb_ds_cs.isEnabled():
            if self.cb_ds_cs.checkState() == QtCore.Qt.Checked:
                for item in self.ds_cs:
                    item.set_visible(True)
            else:
                for item in self.ds_cs:
                    item.set_visible(False)

        if self.cb_final_cs.checkState() == QtCore.Qt.Checked:
            for item in self.final_cs:
                item.set_visible(True)
        else:
            for item in self.final_cs:
                item.set_visible(False)

        # Draw canvas
        self.canvas.draw()

    def update_annot(self, ind, plt_ref, ref_label):
        """Updates the location and text and makes visible the previously initialized and hidden annotation.

        Parameters
        ----------
        ind: dict
            Contains data selected.
        plt_ref: Line2D
            Reference containing plotted data
        ref_label: str
            Label used to ID data type in annotation
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
        text = 'x: {:.2f}, {}: {:.2f}'.format(pos[0], ref_label, pos[1])
        self.annot.set_text(text)

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

        # Determine if mouse location references a data point in the plot and update the annotation.
        if event.inaxes == self.fig.ax:
            cont_final = False
            cont_vb = False
            cont_ds = False
            cont_4b = False
            if self.final_cs is not None:
                cont_final, ind_final = self.final_cs[0].contains(event)
            if self.vb_cs is not None:
                cont_vb, ind_vb = self.vb_cs[0].contains(event)
            if self.ds_cs is not None:
                cont_ds, ind_ds = self.ds_cs[0].contains(event)
            if self.beam_cs is not None:
                cont_4b, ind_4b = self.beam_cs[0].contains(event)

            if cont_final and self.final_cs[0].get_visible():
                self.update_annot(ind_final, self.final_cs[0], 'Final')
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_vb and self.vb_cs[0].get_visible():
                self.update_annot(ind_vb, self.vb_cs[0], 'VB')
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_ds and self.ds_cs[0].get_visible():
                self.update_annot(ind_ds, self.ds_cs[0], 'DS')
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_4b and self.beam_cs[0].get_visible():
                self.update_annot(ind_4b, self.beam_cs[0], 'DS')
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
