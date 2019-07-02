from PyQt5 import QtCore
import numpy as np


class Shiptrack(object):
    """Class to generate shiptrack plot. If checkboxes for the boat reference
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
        cb_vectors: QCheckBox
            Name of QCheckBox for vectors
        bt: list
            Plot reference for bottom track
        gga: list
            Plot reference for GGA
        vtg: list
            Plot reference for VTG
        vectors: list
            Plot reference for vectors
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
        self.cb_vectors = None
        self.bt = None
        self.gga = None
        self.vtg = None
        self.vectors = None

    def create(self, transect, units,
               cb=False, cb_bt=None, cb_gga=None, cb_vtg=None, cb_vectors=None, invalid_bt=None, invalid_gps=None):
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
        cb_vectors: QCheckBox
            Name of QCheckBox for vectors
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
        self.cb_vectors = cb_vectors

        # Check the checkbox to determine what should be shown in the plot
        control = self.checkbox_control(transect)

        # Clear the plot
        self.fig.clear()

        # Configure axis
        self.fig.ax = self.fig.add_subplot(1, 1, 1)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.18, bottom=0.1, right=0.98, top=0.98, wspace=0.1, hspace=0)
        self.fig.ax.xaxis.label.set_fontsize(12)
        self.fig.ax.yaxis.label.set_fontsize(12)

        # Initialize max/min trackers
        max_x_vtg = np.nan
        max_y_vtg = np.nan
        min_x_vtg = np.nan
        min_y_vtg = np.nan
        max_x_gga = np.nan
        max_y_gga = np.nan
        min_x_gga = np.nan
        min_y_gga = np.nan

        # Plot shiptrack based on bottom track
        ship_data_bt = transect.boat_vel.compute_boat_track(transect, ref='bt_vel')
        self.bt = self.fig.ax.plot(ship_data_bt['track_x_m'] * units['L'], ship_data_bt['track_y_m'] * units['L'],
                                   color='r',
                                   label='BT')

        # Plot invalid data points using a symbol to represent what caused the data to be invalid
        if invalid_bt is not None:
            self.bt.append(self.fig.ax.plot(ship_data_bt['track_x_m'][invalid_bt[1]] * units['L'],
                                            ship_data_bt['track_y_m'][invalid_bt[1]] * units['L'],
                                            'k', linestyle='', marker='$O$')[0])
            self.bt.append(self.fig.ax.plot(ship_data_bt['track_x_m'][invalid_bt[2]] * units['L'],
                                            ship_data_bt['track_y_m'][invalid_bt[2]] * units['L'],
                                            'k', linestyle='', marker='$E$')[0])
            self.bt.append(self.fig.ax.plot(ship_data_bt['track_x_m'][invalid_bt[3]] * units['L'],
                                            ship_data_bt['track_y_m'][invalid_bt[3]] * units['L'],
                                            'k', linestyle='', marker='$V$')[0])
            self.bt.append(self.fig.ax.plot(ship_data_bt['track_x_m'][invalid_bt[4]] * units['L'],
                                            ship_data_bt['track_y_m'][invalid_bt[4]] * units['L'],
                                            'k', linestyle='', marker='$S$')[0])
            self.bt.append(self.fig.ax.plot(ship_data_bt['track_x_m'][invalid_bt[5]] * units['L'],
                                            ship_data_bt['track_y_m'][invalid_bt[5]] * units['L'],
                                            'k', linestyle='', marker='$B$')[0])

        ship_data = ship_data_bt
        max_x_bt = np.nanmax(ship_data_bt['track_x_m'])
        max_y_bt = np.nanmax(ship_data_bt['track_y_m'])
        min_x_bt = np.nanmin(ship_data_bt['track_x_m'])
        min_y_bt = np.nanmin(ship_data_bt['track_y_m'])

        # Based on checkbox control make bt visible or not
        if control['bt']:
            for item in self.bt:
                item.set_visible(True)
        else:
            for item in self.bt:
                item.set_visible(False)

        # Plot shiptrack based on vtg, if available
        if transect.boat_vel.vtg_vel is not None:
            ship_data_vtg = transect.boat_vel.compute_boat_track(transect, ref='vtg_vel')
            self.vtg = self.fig.ax.plot(ship_data_vtg['track_x_m'] * units['L'],
                                        ship_data_vtg['track_y_m'] * units['L'],
                                        color='g', label='VTG')

            # Plot invalid data points using a symbol to represent what caused the data to be invalid
            if invalid_gps is not None and not np.alltrue(np.isnan(ship_data_vtg['track_x_m'])):
                self.vtg.append(self.fig.ax.plot(ship_data_vtg['track_x_m'][invalid_gps[1]] * units['L'],
                                                 ship_data_vtg['track_y_m'][invalid_gps[1]] * units['L'],
                                                 'k', linestyle='', marker='$O$')[0])
                self.vtg.append(self.fig.ax.plot(ship_data_vtg['track_x_m'][invalid_gps[4]] * units['L'],
                                                 ship_data_vtg['track_y_m'][invalid_gps[4]] * units['L'],
                                                 'k', linestyle='', marker='$S$')[0])
                self.vtg.append(self.fig.ax.plot(ship_data_vtg['track_x_m'][invalid_gps[5]] * units['L'],
                                                 ship_data_vtg['track_y_m'][invalid_gps[5]] * units['L'],
                                                 'k', linestyle='', marker='$H$')[0])

            if transect.boat_vel.selected == 'vtg_vel':
                ship_data = ship_data_vtg

            if control['vtg']:
                for item in self.vtg:
                    item.set_visible(True)
            else:
                for item in self.vtg:
                    item.set_visible(False)

            max_x_vtg = np.nanmax(ship_data_vtg['track_x_m'])
            max_y_vtg = np.nanmax(ship_data_vtg['track_y_m'])
            min_x_vtg = np.nanmin(ship_data_vtg['track_x_m'])
            min_y_vtg = np.nanmin(ship_data_vtg['track_y_m'])

        # Plot shiptrack based on gga, if available
        if transect.boat_vel.gga_vel is not None:
            ship_data_gga = transect.boat_vel.compute_boat_track(transect, ref='gga_vel')
            self.gga = self.fig.ax.plot(ship_data_gga['track_x_m'] * units['L'],
                                        ship_data_gga['track_y_m'] * units['L'],
                                        color='b', label='GGA')

            # Plot invalid data points using a symbol to represent what caused the data to be invalid
            if invalid_gps is not None and not np.alltrue(np.isnan(ship_data_gga['track_x_m'])):
                self.gga.append(self.fig.ax.plot(ship_data_gga['track_x_m'][invalid_gps[1]] * units['L'],
                                                ship_data_gga['track_y_m'][invalid_gps[1]] * units['L'],
                                                'k', linestyle='', marker='$O$')[0])
                self.gga.append(self.fig.ax.plot(ship_data_gga['track_x_m'][invalid_gps[2]] * units['L'],
                                                ship_data_gga['track_y_m'][invalid_gps[2]] * units['L'],
                                                'k', linestyle='', marker='$Q$')[0])
                self.gga.append(self.fig.ax.plot(ship_data_gga['track_x_m'][invalid_gps[3]] * units['L'],
                                                ship_data_gga['track_y_m'][invalid_gps[3]] * units['L'],
                                                'k', linestyle='', marker='$A$')[0])
                self.gga.append(self.fig.ax.plot(ship_data_gga['track_x_m'][invalid_gps[4]] * units['L'],
                                                ship_data_gga['track_y_m'][invalid_gps[4]] * units['L'],
                                                'k', linestyle='', marker='$S$')[0])
                self.gga.append(self.fig.ax.plot(ship_data_gga['track_x_m'][invalid_gps[5]] * units['L'],
                                                ship_data_gga['track_y_m'][invalid_gps[5]] * units['L'],
                                                'k', linestyle='', marker='$H$')[0])

            if transect.boat_vel.selected == 'gga_vel':
                ship_data = ship_data_gga

            if control['gga']:
                for item in self.gga:
                    item.set_visible(True)
            else:
                for item in self.gga:
                    item.set_visible(False)

            max_x_gga = np.nanmax(ship_data_gga['track_x_m'])
            max_y_gga = np.nanmax(ship_data_gga['track_y_m'])
            min_x_gga = np.nanmin(ship_data_gga['track_x_m'])
            min_y_gga = np.nanmin(ship_data_gga['track_y_m'])

        # Customize axes
        self.fig.ax.set_xlabel(self.canvas.tr('Distance East ') + units['label_L'])
        self.fig.ax.set_ylabel(self.canvas.tr('Distance North ') + units['label_L'])

        self.fig.ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)
        self.fig.ax.grid()
        self.fig.ax.axis('equal')
        for label in (self.fig.ax.get_xticklabels() + self.fig.ax.get_yticklabels()):
            label.set_fontsize(10)

        max_x = np.nanmax([max_x_bt, max_x_gga, max_x_vtg])
        min_x = np.nanmin([min_x_bt, min_x_gga, min_x_vtg])
        max_x = max_x + (max_x - min_x) * 0.1
        min_x = min_x - (max_x - min_x) * 0.1
        max_y = np.nanmax([max_y_bt, max_y_gga, max_y_vtg])
        min_y = np.nanmin([min_y_bt, min_y_gga, min_y_vtg])
        max_y = max_y + (max_y - min_y) * 0.1
        min_y = min_y - (max_y - min_y) * 0.1

        self.fig.ax.set_ylim(top=np.ceil(max_y * units['L']), bottom=np.ceil(min_y * units['L']))
        self.fig.ax.set_xlim(left=np.ceil(min_x * units['L']), right=np.ceil(max_x * units['L']))

        # Compute mean water velocity for each ensemble
        u = transect.w_vel.u_processed_mps
        v = transect.w_vel.v_processed_mps
        u_mean = np.nanmean(u, axis=0)
        v_mean = np.nanmean(v, axis=0)

        # Plot water vectors
        self.vectors = self.fig.ax.quiver(ship_data['track_x_m'] * units['L'], ship_data['track_y_m'] * units['L'],
                                          u_mean * units['V'], v_mean * units['V'], units='dots', width=1, scale=0.6)

        if control['vectors']:
            self.vectors.set_visible(True)
        else:
            self.vectors.set_visible(False)
        # qk = ax.quiverkey(quiv_plt, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
        #                    coordinates='figure')

        self.canvas.draw()

    def change(self):
        """Updates what boat reference tracks are displayed based on the checkboxes.
        """

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
            # Vectors
            if self.cb_vectors.checkState() == QtCore.Qt.Checked:
                self.vectors.set_visible(True)
            else:
                self.vectors.set_visible(False)

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
