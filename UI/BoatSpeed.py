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

    def create(self, transect, units, cb=False, cb_bt=None, cb_gga=None, cb_vtg=None):
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
        self.fig.subplots_adjust(left=0.1, bottom=0.05, right=0.98, top=0.98, wspace=0.1, hspace=0)
        self.fig.ax.set_xlabel(self.canvas.tr('Ensembles'))
        self.fig.ax.set_ylabel(self.canvas.tr('Boat speed' + units['label_V']))
        self.fig.ax.grid()
        self.fig.ax.xaxis.label.set_fontsize(12)
        self.fig.ax.yaxis.label.set_fontsize(12)
        self.fig.ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)

        # Initialize max trackers
        max_gga = np.nan
        max_vtg = np.nan

        # Plot bottom track boat speed
        speed = np.sqrt(transect.boat_vel.bt_vel.u_processed_mps ** 2 + transect.boat_vel.bt_vel.v_processed_mps ** 2)
        self.bt = self.fig.ax.plot(speed * units['V'], 'r-')
        max_bt = np.nanmax(speed)
        if control['bt']:
            self.bt[0].set_visible(True)
        else:
            self.bt[0].set_visible(False)

        # Plot VTG boat speed
        if transect.boat_vel.vtg_vel is not None:
            speed = np.sqrt(
                transect.boat_vel.vtg_vel.u_processed_mps ** 2 + transect.boat_vel.vtg_vel.v_processed_mps ** 2)
            self.vtg = self.fig.ax.plot(speed * units['V'], 'g-')
            max_vtg = np.nanmax(speed)
            if control['vtg']:
                self.vtg[0].set_visible(True)
            else:
                self.vtg[0].set_visible(False)

        # Plot GGA boat speed
        if transect.boat_vel.gga_vel is not None:
            speed = np.sqrt(
                transect.boat_vel.gga_vel.u_processed_mps ** 2 + transect.boat_vel.gga_vel.v_processed_mps ** 2)
            self.gga = self.fig.ax.plot(speed * units['V'], 'b-')
            max_gga = np.nanmax(speed)
            if control['gga']:
                self.gga[0].set_visible(True)
            else:
                self.gga[0].set_visible(False)

        # Set axis limits
        max_y = np.nanmax([max_bt, max_gga, max_vtg]) * 1.1
        self.fig.ax.set_ylim(top=np.ceil(max_y * units['L']), bottom=0)

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
                self.bt[0].set_visible(True)
            else:
                self.bt[0].set_visible(False)
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
