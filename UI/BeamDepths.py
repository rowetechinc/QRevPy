from PyQt5 import QtCore
import numpy as np


class BeamDepths(object):
    """Class to generate cross section using the depths of each beam available.
    What beams are plotted are controlled by the user through checkboxes.

    Attributes
    ----------
    canvas: MplCanvas
        Object of MplCanvas a FigureCanvas
    fig: Object
        Figure object of the canvas
    units: dict
        Dictionary of units conversions
    cb_beam1: QCheckBox
        Checkbox to plot beam 1
    cb_beam2: QCheckBox
        Checkbox to plot beam 2
    cb_beam3: QCheckBox
        Checkbox to plot beam 3
    cb_beam4: QCheckBox
        Checkbox to plot beam 4
    cb_vert: QCheckBox
        Checkbox to plot vertical beam
    cb_ds: QCheckBox
        Checkbox to plot depth sounder
    beam1: list
        Plot reference for beam 1
    beam2: list
        Plot reference for beam 2
    beam3: list
        Plot reference for beam 3
    beam4: list
        Plot reference for beam 4
    vb: list
        Plot reference for vertical beam
    ds: list
        Plot reference for depth sounder
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
        self.cb_beam1 = None
        self.cb_beam2 = None
        self.cb_beam3 = None
        self.cb_beam4 = None
        self.cb_vert = None
        self.cb_ds = None
        self.beam1 = None
        self.beam2 = None
        self.beam3 = None
        self.beam4 = None
        self.vb = None
        self.ds = None
        self.hover_connection = None

    def create(self, transect, units,
               cb_beam1=None,
               cb_beam2=None,
               cb_beam3=None,
               cb_beam4=None,
               cb_vert=None,
               cb_ds=None):

        """Create the axes and lines for the figure.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData containing boat speeds to be plotted
        units: dict
            Dictionary of units conversions
        cb_beam1: QCheckBox
            Checkbox to plot beam 1
        cb_beam2: QCheckBox
            Checkbox to plot beam 2
        cb_beam3: QCheckBox
            Checkbox to plot beam 3
        cb_beam4: QCheckBox
            Checkbox to plot beam 4
        cb_vert: QCheckBox
            Checkbox to plot vertical beam
        cb_ds: QCheckBox
            Checkbox to plot depth sounder
        """

        # Assign and save parameters
        self.cb_beam1 = cb_beam1
        self.cb_beam2 = cb_beam2
        self.cb_beam3 = cb_beam3
        self.cb_beam4 = cb_beam4
        self.cb_vert = cb_vert
        self.cb_ds = cb_ds

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
        max_vert = np.nan
        max_ds = np.nan

        # Compute x axis data
        boat_track = transect.boat_vel.compute_boat_track(transect=transect)
        if not np.alltrue(np.isnan(boat_track['track_x_m'])):
            x = boat_track['distance_m']
            invalid_beams = np.logical_not(transect.depths.bt_depths.valid_beams)
            beam_depths = transect.depths.bt_depths.depth_beams_m

            # Plot beams
            self.beam1 = self.fig.ax.plot(x * units['L'],
                                          beam_depths[0, :] * units['L'],
                                          'r-')
            self.beam1.append(self.fig.ax.plot(x[invalid_beams[0, :]] * units['L'],
                                               beam_depths[0, invalid_beams[0, :]] * units['L'],
                                               'r', linestyle='',
                                               marker='$O$')[0])

            self.beam2 = self.fig.ax.plot(x * units['L'],
                                          beam_depths[1, :] * units['L'],
                                          color='#005500')
            self.beam2.append(self.fig.ax.plot(x[invalid_beams[1, :]] * units['L'],
                                               beam_depths[1, invalid_beams[1, :]] * units['L'],
                                               color='#005500',
                                               linestyle='-',
                                               marker='$O$')[0])

            self.beam3 = self.fig.ax.plot(x * units['L'],
                                          beam_depths[2, :] * units['L'],
                                          'b-')
            self.beam3.append(self.fig.ax.plot(x[invalid_beams[2, :]] * units['L'],
                                               beam_depths[2, invalid_beams[2, :]] * units['L'],
                                               'b',
                                               linestyle='-',
                                               marker='$O$')[0])

            self.beam4 = self.fig.ax.plot(x * units['L'],
                                          beam_depths[3, :] * units['L'],
                                          color='#aa5500',
                                          linestyle='-')
            self.beam4.append(self.fig.ax.plot(x[invalid_beams[3, :]] * units['L'],
                                               beam_depths[3, invalid_beams[3, :]] * units['L'],
                                               color='#aa5500',
                                               linestyle='',
                                               marker='$O$')[0])
            # Compute max depth from beams
            max_beams = np.nanmax(np.nanmax(transect.depths.bt_depths.depth_beams_m))

            # Based on checkbox control make beams visible or not
            if cb_beam1.checkState() == QtCore.Qt.Checked:
                for item in self.beam1:
                    item.set_visible(True)
            else:
                for item in self.beam1:
                    item.set_visible(False)

            if cb_beam2.checkState() == QtCore.Qt.Checked:
                for item in self.beam2:
                    item.set_visible(True)
            else:
                for item in self.beam2:
                    item.set_visible(False)

            if cb_beam3.checkState() == QtCore.Qt.Checked:
                for item in self.beam3:
                    item.set_visible(True)
            else:
                for item in self.beam3:
                    item.set_visible(False)

            if cb_beam4.checkState() == QtCore.Qt.Checked:
                for item in self.beam4:
                    item.set_visible(True)
            else:
                for item in self.beam4:
                    item.set_visible(False)

            # Plot vertical beam
            if transect.depths.vb_depths is not None:
                invalid_beams = np.logical_not(transect.depths.vb_depths.valid_beams[0, :])
                beam_depths = transect.depths.vb_depths.depth_beams_m[0, :]
                self.vb = self.fig.ax.plot(x * units['L'],
                                           beam_depths * units['L'],
                                           color='#aa00ff',
                                           linestyle='-')
                self.vb.append(self.fig.ax.plot(x[invalid_beams] * units['L'],
                                                beam_depths[invalid_beams] * units['L'],
                                                color='#aa00ff',
                                                linestyle='',
                                                marker='$O$')[0])

                if cb_vert.checkState() == QtCore.Qt.Checked:
                    for item in self.vb:
                        item.set_visible(True)
                else:
                    for item in self.vb:
                        item.set_visible(False)

                max_vert = np.nanmax(beam_depths)

                # Plot depth sounder
                if transect.depths.ds_depths is not None:
                    invalid_beams = np.logical_not(transect.depths.ds_depths.valid_beams[0, :])
                    beam_depths = transect.depths.ds_depths.depth_beams_m[0, :]
                    self.ds = self.fig.ax.plot(x * units['L'],
                                               beam_depths * units['L'],
                                               color='#00aaff')
                    self.ds.append(self.fig.ax.plot(x[invalid_beams] * units['L'],
                                                    beam_depths[invalid_beams] * units['L'],
                                                    color='#00aaff',
                                                    linestyle='',
                                                    marker='$O$')[0])

                    if cb_ds.checkState() == QtCore.Qt.Checked:
                        for item in self.ds:
                            item.set_visible(True)
                    else:
                        for item in self.ds:
                            item.set_visible(False)

                    max_ds = np.nanmax(beam_depths)

            # Set axis limits
            max_y = np.nanmax([max_beams, max_vert, max_ds]) * 1.1
            self.fig.ax.invert_yaxis()
            self.fig.ax.set_ylim(bottom=np.ceil(max_y * units['L']), top=0)
            self.fig.ax.set_xlim(left=-1 * x[-1] * 0.02 * units['L'], right=x[-1] * 1.02 * units['L'])
            if transect.start_edge == 'Right':
                self.fig.ax.invert_xaxis()
                self.fig.ax.set_xlim(right=-1 * x[-1] * 0.02 * units['L'], left=x[-1] * 1.02 * units['L'])

            self.annot = self.fig.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                              bbox=dict(boxstyle="round", fc="w"),
                                              arrowprops=dict(arrowstyle="->"))

            self.annot.set_visible(False)

            self.canvas.draw()

    def change(self):
        """Changes the visibility of the available beams based on user input via checkboxes.
        """

        # Set visibility of beams based on user input
        if self.cb_beam1.checkState() == QtCore.Qt.Checked:
            for item in self.beam1:
                item.set_visible(True)
        else:
            for item in self.beam1:
                item.set_visible(False)

        if self.cb_beam2.checkState() == QtCore.Qt.Checked:
            for item in self.beam2:
                item.set_visible(True)
        else:
            for item in self.beam2:
                item.set_visible(False)

        if self.cb_beam3.checkState() == QtCore.Qt.Checked:
            for item in self.beam3:
                item.set_visible(True)
        else:
            for item in self.beam3:
                item.set_visible(False)

        if self.cb_beam4.checkState() == QtCore.Qt.Checked:
            for item in self.beam4:
                item.set_visible(True)
        else:
            for item in self.beam4:
                item.set_visible(False)

        if self.cb_vert.isEnabled():
            if self.cb_vert.checkState() == QtCore.Qt.Checked:
                for item in self.vb:
                    item.set_visible(True)
            else:
                for item in self.vb:
                    item.set_visible(False)

        if self.cb_ds.isEnabled():
            if self.cb_ds.checkState() == QtCore.Qt.Checked:
                for item in self.ds:
                    item.set_visible(True)
            else:
                for item in self.ds:
                    item.set_visible(False)

        # Draw canvas
        self.canvas.draw()

    def update_annot(self, ind, plt_ref, ref_label):

        # pos = plt_ref.get_offsets()[ind["ind"][0]]
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
        text = 'x: {:.2f}, {}: {:.2f}'.format(pos[0], ref_label, pos[1])
        self.annot.set_text(text)

    def hover(self, event):
        vis = self.annot.get_visible()
        if event.inaxes == self.fig.ax:
            cont_beam1 = False
            cont_beam2 = False
            cont_beam3 = False
            cont_beam4 = False
            cont_vb = False
            cont_ds = False
            if self.beam1 is not None:
                cont_beam1, ind_beam1 = self.beam1[0].contains(event)
            if self.beam2 is not None:
                cont_beam2, ind_beam2 = self.beam2[0].contains(event)
            if self.beam3 is not None:
                cont_beam3, ind_beam3 = self.beam3[0].contains(event)
            if self.beam4 is not None:
                cont_beam4, ind_beam4 = self.beam4[0].contains(event)
            if self.vb is not None:
                cont_vb, ind_vb = self.vb[0].contains(event)
            if self.ds is not None:
                cont_ds, ind_ds = self.ds[0].contains(event)
            if cont_beam1 and self.beam1[0].get_visible():
                self.update_annot(ind_beam1, self.beam1[0], 'B1')
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_beam2 and self.beam2[0].get_visible():
                self.update_annot(ind_beam2, self.beam2[0], 'B2')
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_beam3 and self.beam3[0].get_visible():
                self.update_annot(ind_beam3, self.beam3[0], 'B3')
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            if cont_beam4 and self.beam4[0].get_visible():
                self.update_annot(ind_beam4, self.beam4[0], 'B4')
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_vb and self.vb[0].get_visible():
                self.update_annot(ind_vb, self.vb[0], 'VB')
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_ds and self.ds[0].get_visible():
                self.update_annot(ind_ds, self.ds[0], 'VTG')
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
