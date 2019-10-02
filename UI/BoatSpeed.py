from PyQt5 import QtCore
import numpy as np


class BoatSpeed(object):
    """Class to generate boat speed time series plot. If checkboxes for the boat speed reference
    (BT, GGA, VTG) are available they can be used to control what references are plotted.

    Attributes
    ----------
    canvas: MplCanvas
        Object of MplCanvas a FigureCanvas
    fig: Object
        Figure object of the canvas
    units: dict
        Dictionary of units conversions
    cb: bool
        Boolean to determine if checkboxes to control the boat speed reference are to be used
    cb_bt: QCheckBox
        Name of QCheckBox for bottom track
    cb_gga: QCheckBox
        Name of QCheckBox for GGA
    cb_vtg: QCheckBox
        Name of QCheckBox for VTG
    bt: list
        Plot reference for bottom track
    gga: list
        Plot reference for GGA
    vtg: list
        Plot reference for VTG
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
        self.cb = None
        self.cb_bt = None
        self.cb_gga = None
        self.cb_vtg = None
        self.bt = None
        self.gga = None
        self.vtg = None
        self.hover_connection = None

    def create(self, transect, units,
               cb=False, cb_bt=None, cb_gga=None, cb_vtg=None, invalid_bt=None, invalid_gps=None):
        """Create the axes and lines for the figure.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData containing boat speeds to be plotted
        units: dict
            Dictionary of units conversions
        cb: bool
            Boolean to determine if checkboxes to control the boat speed reference are to be used
        cb_bt: QCheckBox
            Name of QCheckBox for bottom track
        cb_gga: QCheckBox
            Name of QCheckBox for GGA
        cb_vtg: QCheckBox
            Name of QCheckBox for VTG
        invalid_bt: np.array(bool)
            Boolean array of invalid data based on filters for bottom track
        invalid_gps: np.array(bool)
            Boolean array of invalid data based on filters for gps data
        """

        # Assign and save parameters
        self.units = units
        self.cb = cb
        self.cb_bt = cb_bt
        self.cb_gga = cb_gga
        self.cb_vtg = cb_vtg

        # Check the checkbox to determine what should be shown in the plot
        control = self.checkbox_control(transect)

        # Clear the plot
        self.fig.clear()

        # Configure axis
        self.fig.ax = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.08, bottom=0.2, right=0.98, top=0.98, wspace=0.1, hspace=0)
        self.fig.ax.set_xlabel(self.canvas.tr('Ensembles'))
        self.fig.ax.set_ylabel(self.canvas.tr('Boat speed' + units['label_V']))
        self.fig.ax.grid()
        self.fig.ax.xaxis.label.set_fontsize(12)
        self.fig.ax.yaxis.label.set_fontsize(12)
        self.fig.ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)

        # Initialize max trackers
        max_gga = np.nan
        max_vtg = np.nan

        ensembles = np.arange(1, len(transect.boat_vel.bt_vel.u_mps) + 1)

        # Plot bottom track boat speed
        speed = np.sqrt(transect.boat_vel.bt_vel.u_processed_mps ** 2 + transect.boat_vel.bt_vel.v_processed_mps ** 2)
        self.bt = self.fig.ax.plot(ensembles, speed * units['V'], 'r-')

        # Plot invalid data points using a symbol to represent what caused the data to be invalid
        if invalid_bt is not None:
            self.bt.append(self.fig.ax.plot(ensembles[invalid_bt[1]], speed[invalid_bt[1]] * units['V'],
                                            'k', linestyle='', marker='$O$')[0])
            self.bt.append(self.fig.ax.plot(ensembles[invalid_bt[2]], speed[invalid_bt[2]] * units['V'],
                                            'k', linestyle='', marker='$E$')[0])
            self.bt.append(self.fig.ax.plot(ensembles[invalid_bt[3]], speed[invalid_bt[3]] * units['V'],
                                            'k', linestyle='', marker='$V$')[0])
            self.bt.append(self.fig.ax.plot(ensembles[invalid_bt[4]], speed[invalid_bt[4]] * units['V'],
                                            'k', linestyle='', marker='$S$')[0])
            self.bt.append(self.fig.ax.plot(ensembles[invalid_bt[5]], speed[invalid_bt[5]] * units['V'],
                                            'k', linestyle='', marker='$B$')[0])

        max_bt = np.nanmax(speed)

        # Based on checkbox control make bt visible or not
        if control['bt']:
            for item in self.bt:
                item.set_visible(True)
        else:
            for item in self.bt:
                item.set_visible(False)

        # Plot VTG boat speed
        if transect.boat_vel.vtg_vel is not None:
            speed = np.sqrt(
                transect.boat_vel.vtg_vel.u_processed_mps ** 2 + transect.boat_vel.vtg_vel.v_processed_mps ** 2)
            self.vtg = self.fig.ax.plot(ensembles, speed * units['V'], 'g-')

            # Plot invalid data points using a symbol to represent what caused the data to be invalid
            if invalid_gps is not None:
                self.vtg.append(self.fig.ax.plot(ensembles[invalid_gps[1]], speed[invalid_gps[1]] * units['V'],
                                                'k', linestyle='', marker='$O$')[0])
                self.vtg.append(self.fig.ax.plot(ensembles[invalid_gps[5]], speed[invalid_gps[5]] * units['V'],
                                                'k', linestyle='', marker='$H$')[0])
                self.vtg.append(self.fig.ax.plot(ensembles[invalid_gps[4]], speed[invalid_gps[4]] * units['V'],
                                                'k', linestyle='', marker='$S$')[0])

            max_vtg = np.nanmax(speed)
            if control['vtg']:
                for item in self.vtg:
                    item.set_visible(True)
            else:
                for item in self.vtg:
                    item.set_visible(False)

        # Plot GGA boat speed
        if transect.boat_vel.gga_vel is not None:
            speed = np.sqrt(
                transect.boat_vel.gga_vel.u_processed_mps ** 2 + transect.boat_vel.gga_vel.v_processed_mps ** 2)
            self.gga = self.fig.ax.plot(ensembles, speed * units['V'], 'b-')

            # Plot invalid data points using a symbol to represent what caused the data to be invalid
            if invalid_gps is not None:
                self.gga.append(self.fig.ax.plot(ensembles[invalid_gps[1]], speed[invalid_gps[1]] * units['V'],
                                                 'k', linestyle='', marker='$O$')[0])
                self.gga.append(self.fig.ax.plot(ensembles[invalid_gps[2]], speed[invalid_gps[2]] * units['V'],
                                                 'k', linestyle='', marker='$Q$')[0])
                self.gga.append(self.fig.ax.plot(ensembles[invalid_gps[3]], speed[invalid_gps[3]] * units['V'],
                                                 'k', linestyle='', marker='$A$')[0])
                self.gga.append(self.fig.ax.plot(ensembles[invalid_gps[5]], speed[invalid_gps[5]] * units['V'],
                                                 'k', linestyle='', marker='$H$')[0])
                self.gga.append(self.fig.ax.plot(ensembles[invalid_gps[4]], speed[invalid_gps[4]] * units['V'],
                                                'k', linestyle='', marker='$S$')[0])

            max_gga = np.nanmax(speed)
            if control['gga']:
                for item in self.gga:
                    item.set_visible(True)
            else:
                for item in self.gga:
                    item.set_visible(False)

        # Set axis limits
        max_y = np.nanmax([max_bt, max_gga, max_vtg]) * 1.1
        self.fig.ax.set_ylim(top=np.ceil(max_y * units['L']), bottom=-0.5)
        self.fig.ax.set_xlim(left=-1 * ensembles[-1] * 0.02, right=ensembles[-1] * 1.02)

        if transect.start_edge == 'Right':
            self.fig.ax.invert_xaxis()
            self.fig.ax.set_xlim(right=-1 * ensembles[-1] * 0.02, left=ensembles[-1] * 1.02)

        # Initialize annotation for data cursor
        self.annot = self.fig.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"))

        self.annot.set_visible(False)

        self.canvas.draw()

    def checkbox_control(self, transect):
        """Controls the visibility and checks the status of checkboxes.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData with boat speeds to be plotted.
        """

        # Initialize control dictionary
        control = {'bt': True, 'gga': True, 'vtg': True, 'vectors': True}

        # If checkboxes are available, enable the checkboxes if transect contains that type of data
        if self.cb:
            # Enable check boxes as data is available
            if transect.boat_vel.gga_vel is not None:
                self.cb_gga.setEnabled(True)
            else:
                self.cb_gga.setCheckState(QtCore.Qt.Unchecked)
                self.cb_gga.setEnabled(False)

            if transect.boat_vel.vtg_vel is not None:
                self.cb_vtg.setEnabled(True)
            else:
                self.cb_vtg.setCheckState(QtCore.Qt.Unchecked)
                self.cb_vtg.setEnabled(False)

            # Get checkbox status
            # BT
            if self.cb_bt.checkState() == QtCore.Qt.Checked:
                control['bt'] = True
            else:
                control['bt'] = False
            # GGA
            if self.cb_gga.checkState() == QtCore.Qt.Checked:
                control['gga'] = True
            else:
                control['gga'] = False
            # VTG
            if self.cb_vtg.checkState() == QtCore.Qt.Checked:
                control['vtg'] = True
            else:
                control['vtg'] = False
        return control

    def change(self):
        """Changes the visibility of the various boat speed references based on user input via checkboxes.
        """

        # If checkboxes are available, check status and set boat speed reference line visibility accordingly.
        if self.cb:
            if self.cb_bt.checkState() == QtCore.Qt.Checked:
                for item in self.bt:
                    item.set_visible(True)
            else:
                for item in self.bt:
                    item.set_visible(False)
            # GGA
            if self.cb_gga.checkState() == QtCore.Qt.Checked:
                self.gga[0].set_visible(True)
            else:
                self.gga[0].set_visible(False)
            # VTG
            if self.cb_vtg.checkState() == QtCore.Qt.Checked:
                self.vtg[0].set_visible(True)
            else:
                self.vtg[0].set_visible(False)

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
            cont_bt = False
            cont_gga = False
            cont_vtg = False
            if self.bt is not None:
                cont_bt, ind_bt = self.bt[0].contains(event)
            if self.gga is not None:
                cont_gga, ind_gga = self.gga[0].contains(event)
            if self.vtg is not None:
                cont_vtg, ind_vtg = self.vtg[0].contains(event)
            if cont_bt and self.bt[0].get_visible():
                self.update_annot(ind_bt, self.bt[0], 'BT')
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_gga and self.gga[0].get_visible():
                self.update_annot(ind_gga, self.gga[0], 'GGA')
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_vtg and self.vtg[0].get_visible():
                self.update_annot(ind_vtg, self.vtg[0], 'VTG')
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