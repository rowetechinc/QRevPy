import numpy as np
from PyQt5 import QtCore


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
        hover_connection: int
            Index to data cursor connection
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
        self.vector_ref = None
        self.hover_connection = None
        self.annot = None

    def create(self, transect, units,
               cb=False, cb_bt=None, cb_gga=None, cb_vtg=None, cb_vectors=None,
               n_ensembles=None, edge_start=None):
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
        n_ensembles: int
            Number of ensembles to plot. Used in edges tab.
        edge_start: int
            Ensemble to start plotting. Used in edges tab.
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
        self.fig.subplots_adjust(left=0.18, bottom=0.18, right=0.98, top=0.98, wspace=0.1, hspace=0)
        self.fig.ax.xaxis.label.set_fontsize(12)
        self.fig.ax.yaxis.label.set_fontsize(12)

        # Initialize max/min trackers
        max_x_bt = np.nan
        max_y_bt = np.nan
        min_x_bt = np.nan
        min_y_bt = np.nan
        max_x_vtg = np.nan
        max_y_vtg = np.nan
        min_x_vtg = np.nan
        min_y_vtg = np.nan
        max_x_gga = np.nan
        max_y_gga = np.nan
        min_x_gga = np.nan
        min_y_gga = np.nan

        # Plot shiptrack based on bottom track
        invalid_bt = np.logical_not(transect.boat_vel.bt_vel.valid_data)
        invalid_bt = invalid_bt[:, transect.in_transect_idx]
        ship_data_bt = transect.boat_vel.compute_boat_track(transect, ref='bt_vel')
        if edge_start is not None and n_ensembles is not None:
            ship_data_bt['track_x_m'] = self.subsection(ship_data_bt['track_x_m'], n_ensembles, edge_start)
            ship_data_bt['track_y_m'] = self.subsection(ship_data_bt['track_y_m'], n_ensembles, edge_start)
            invalid_bt = self.subsection_2d(invalid_bt, n_ensembles, edge_start)

        self.bt = self.fig.ax.plot(ship_data_bt['track_x_m'] * units['L'], ship_data_bt['track_y_m'] * units['L'],
                                   color='r',
                                   label='BT')

        if edge_start is not None \
                and not np.alltrue(np.isnan(ship_data_bt['track_x_m'])) \
                and len(ship_data_bt['track_x_m']) > 0:
            if edge_start:
                self.bt.append(self.fig.ax.plot(ship_data_bt['track_x_m'][0] * units['L'],
                                                ship_data_bt['track_y_m'][0] * units['L'], 'sk')[0])
            else:
                self.bt.append(self.fig.ax.plot(ship_data_bt['track_x_m'][-1] * units['L'],
                                                ship_data_bt['track_y_m'][-1] * units['L'], 'sk')[0])

        # Plot invalid data points using a symbol to represent what caused the data to be invalid

        if invalid_bt is not None \
                and not np.alltrue(np.isnan(ship_data_bt['track_x_m'])) \
                and len(ship_data_bt['track_x_m']) > 0:
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
        if len(ship_data_bt['track_x_m']) > 0:
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
            invalid_gps = np.logical_not(transect.boat_vel.vtg_vel.valid_data)
            invalid_gps = invalid_gps[:, transect.in_transect_idx]
            if not np.alltrue(np.isnan(ship_data_vtg['track_x_m'])):
                if edge_start is not None and n_ensembles is not None:
                    ship_data_vtg['track_x_m'] = self.subsection(ship_data_vtg['track_x_m'], n_ensembles, edge_start)
                    ship_data_vtg['track_y_m'] = self.subsection(ship_data_vtg['track_y_m'], n_ensembles, edge_start)
                    invalid_gps = self.subsection_2d(invalid_gps, n_ensembles, edge_start)
                self.vtg = self.fig.ax.plot(ship_data_vtg['track_x_m'] * units['L'],
                                            ship_data_vtg['track_y_m'] * units['L'],
                                            color='g', label='VTG')

                if len(ship_data_vtg['track_x_m']) > 0:
                    if edge_start is not None:
                        if edge_start:
                            self.vtg.append(self.fig.ax.plot(ship_data_vtg['track_x_m'][0] * units['L'],
                                                             ship_data_vtg['track_y_m'][0] * units['L'], 'sk')[0])
                        else:
                            self.vtg.append(self.fig.ax.plot(ship_data_vtg['track_x_m'][-1] * units['L'],
                                                             ship_data_vtg['track_y_m'][-1] * units['L'], 'sk')[0])

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
            invalid_gps = np.logical_not(transect.boat_vel.gga_vel.valid_data)
            invalid_gps = invalid_gps[:, transect.in_transect_idx]
            if not np.alltrue(np.isnan(ship_data_gga['track_x_m'])):
                if edge_start is not None and n_ensembles is not None:
                    ship_data_gga['track_x_m'] = self.subsection(ship_data_gga['track_x_m'], n_ensembles, edge_start)
                    ship_data_gga['track_y_m'] = self.subsection(ship_data_gga['track_y_m'], n_ensembles, edge_start)
                    invalid_gps = self.subsection_2d(invalid_gps, n_ensembles, edge_start)
                self.gga = self.fig.ax.plot(ship_data_gga['track_x_m'] * units['L'],
                                            ship_data_gga['track_y_m'] * units['L'],
                                            color='b', label='GGA')

                if len(ship_data_gga['track_x_m']) > 0:
                    if edge_start is not None:
                        try:
                            if edge_start:
                                self.gga.append(self.fig.ax.plot(ship_data_gga['track_x_m'][0] * units['L'],
                                                                 ship_data_gga['track_y_m'][0] * units['L'], 'sk')[0])
                            else:
                                self.gga.append(self.fig.ax.plot(ship_data_gga['track_x_m'][-1] * units['L'],
                                                                 ship_data_gga['track_y_m'][-1] * units['L'], 'sk')[0])
                        except TypeError:
                            pass

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

        if n_ensembles is not None:
            if transect.w_vel.nav_ref == 'BT':
                max_x = max_x_bt
                min_x = min_x_bt
                max_y = max_y_bt
                min_y = min_y_bt
            elif transect.w_vel.nav_ref == 'GGA':
                max_x = max_x_gga
                min_x = min_x_gga
                max_y = max_y_gga
                min_y = min_y_gga
            elif transect.w_vel.nav_ref == 'VTG':
                max_x = max_x_vtg
                min_x = min_x_vtg
                max_y = max_y_vtg
                min_y = min_y_vtg
            max_x = max_x + (max_x - min_x) * 0.1
            min_x = min_x - (max_x - min_x) * 0.1
            max_y = max_y + (max_y - min_y) * 0.1
            min_y = min_y - (max_y - min_y) * 0.1

            if np.logical_not(np.any(np.isnan(np.array([max_x, min_x, max_y, min_y])))):
                self.fig.ax.set_ylim(top=(max_y * units['L']), bottom=(min_y * units['L']))
                self.fig.ax.set_xlim(left=(min_x * units['L']), right=(max_x * units['L']))
        else:
            if np.logical_not(np.any(np.isnan(np.array([max_x, min_x, max_y, min_y])))):
                self.fig.ax.set_ylim(top=np.ceil(max_y * units['L']), bottom=np.ceil(min_y * units['L']))
                self.fig.ax.set_xlim(left=np.ceil(min_x * units['L']), right=np.ceil(max_x * units['L']))

        # Compute mean water velocity for each ensemble
        u = np.copy(transect.w_vel.u_processed_mps)
        v = np.copy(transect.w_vel.v_processed_mps)
        self.vector_ref = transect.w_vel.nav_ref

        if edge_start is not None and n_ensembles is not None:
            u[np.logical_not(transect.w_vel.valid_data[0, :, :])] = np.nan
            v[np.logical_not(transect.w_vel.valid_data[0, :, :])] = np.nan
            u_mean = np.nanmean(u, axis=0)
            v_mean = np.nanmean(v, axis=0)
            u_mean = self.subsection(u_mean, n_ensembles, edge_start)
            v_mean = self.subsection(v_mean, n_ensembles, edge_start)
        else:
            u_mean = np.nanmean(u, axis=0)
            v_mean = np.nanmean(v, axis=0)

        speed = np.sqrt(u_mean**2 + v_mean**2) * units['V']
        if len(speed) > 0:
            max_speed = np.nanmax(speed)
        else:
            max_speed = 0
        # Plot water vectors
        if len(ship_data['track_x_m']) > 0:
            self.vectors = self.fig.ax.quiver(ship_data['track_x_m'] * units['L'], ship_data['track_y_m'] * units['L'],
                                              u_mean * units['V'], v_mean * units['V'], units='dots', width=1,
                                              scale_units='width', scale=4*max_speed)
            if control['vectors']:
                self.vectors.set_visible(True)
            else:
                self.vectors.set_visible(False)

        # Initialize annotation for data cursor
        self.annot = self.fig.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                          bbox=dict(boxstyle="round", fc="w"),
                                          arrowprops=dict(arrowstyle="->"))

        self.annot.set_visible(False)

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
            if self.cb_gga.checkState() == QtCore.Qt.Checked and self.gga is not None:
                for item in self.gga:
                    item.set_visible(True)
            elif self.gga is not None:
                for item in self.gga:
                    item.set_visible(False)
            # VTG
            if self.cb_vtg.checkState() == QtCore.Qt.Checked and self.vtg is not None:
                for item in self.vtg:
                    item.set_visible(True)
            elif self.vtg is not None:
                for item in self.vtg:
                    item.set_visible(False)
            # Vectors
            if self.cb_vectors.checkState() == QtCore.Qt.Checked:
                self.vectors.set_visible(True)
            else:
                self.vectors.set_visible(False)

        self.canvas.draw()

    @staticmethod
    def subsection(data, n_ensembles, edge_start):
        """Subsections data for shiptrack of edge ensembles.

        Parameters
        ----------
        data: np.ndarray(float)
            Shiptrack coordinate
        n_ensembles: int
            Number of ensembles in subsection
        edge_start: int
            Identifies start bank
        """

        # if np.all(np.isnan(data)):
        #     data_out = data
        # else:
        #     if edge_start:
        #         data_out = data[:int(n_ensembles)]
        #     else:
        #         data_out = data[-int(n_ensembles):]
        if n_ensembles > 0:
            if data is not np.nan and len(data) > int(n_ensembles):
                if edge_start:
                    data_out = data[:int(n_ensembles)]
                else:
                    data_out = data[-int(n_ensembles):]
            else:
                data_out = data
        else:
            data_out = np.array([])
        return data_out

    @staticmethod
    def subsection_2d(data, n_ensembles, edge_start):
        """Subsections data for shiptrack of edge ensembles.

        Parameters
        ----------
        data: np.ndarray(float)
            Shiptrack coordinate
        n_ensembles: int
            Number of ensembles in subsection
        edge_start: int
            Identifies start bank
        """
        if data.shape[1] > int(n_ensembles):
            if edge_start:
                data_out = data[:,:int(n_ensembles)]
            else:
                data_out = data[:,-int(n_ensembles):]
        else:
            data_out = data
        return data_out

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
            if self.cb_bt.checkState():
                control['bt'] = True
            else:
                control['bt'] = False
            # GGA
            if self.cb_gga.checkState():
                control['gga'] = True
            else:
                control['gga'] = False
            # VTG
            if self.cb_vtg.checkState():
                control['vtg'] = True
            else:
                control['vtg'] = False
            if self.cb_vectors.checkState() == QtCore.Qt.Checked:
                control['vectors'] = True
            else:
                control['vectors'] = False

        return control

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
            cont_bt = False
            cont_gga = False
            cont_vtg = False
            ind_bt = None
            ind_gga = None
            ind_vtg = None
            if self.bt is not None:
                cont_bt, ind_bt = self.bt[0].contains(event)
            if self.gga is not None:
                cont_gga, ind_gga = self.gga[0].contains(event)
            if self.vtg is not None:
                cont_vtg, ind_vtg = self.vtg[0].contains(event)

            if cont_bt and self.bt[0].get_visible():
                self.update_annot(ind_bt, self.bt[0], self.vectors, 'BT')
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_gga and self.gga[0].get_visible():
                self.update_annot(ind_gga, self.gga[0], self.vectors, 'GGA')
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            elif cont_vtg and self.vtg[0].get_visible():
                self.update_annot(ind_vtg, self.vtg[0], self.vectors, 'VTG')
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
            self.hover_connection = self.canvas.mpl_connect('button_press_event', self.hover)
        elif not setting:
            self.canvas.mpl_disconnect(self.hover_connection)
            self.hover_connection = None
            self.annot.set_visible(False)
            self.canvas.draw_idle()

    def update_annot(self, ind, plt_ref, vector_ref, ref_label):
        """Updates the location and text and makes visible the previously initialized and hidden annotation.

        Parameters
        ----------
        ind: dict
            Contains data selected.
        plt_ref: Line2D
            Reference containing plotted data
        vector_ref: Quiver
            Refernece containing plotted data
        ref_label: str
            Label used to ID data type in annotation
        """

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
        if self.vector_ref == ref_label:
            v = np.sqrt(vector_ref.U[ind["ind"][0]]**2 + vector_ref.V[ind["ind"][0]]**2)
            text = '{} x: {:.2f}, y: {:.2f}, \n v: {:.1f}'.format(ref_label, pos[0], pos[1], v)
        else:
            text = '{} x: {:.2f}, y: {:.2f}'.format(ref_label, pos[0], pos[1])
        self.annot.set_text(text)
