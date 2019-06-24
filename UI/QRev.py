from PyQt5 import QtWidgets, QtCore, QtGui
# from Classes.stickysettings import StickySettings as SSet
from PyQt5.QtCore import pyqtSignal, QRegExp

import UI.QRev_gui as QRev_gui
import sys
import threading
from UI.selectFile import OpenMeasurementDialog, SaveMeasurementDialog
from Classes.Measurement import Measurement
from Classes.Python2Matlab import Python2Matlab
from Classes.Sensors import Sensors
from Classes.MovingBedTests import MovingBedTests
import numpy as np
from UI.Qtmpl import Qtmpl
from MiscLibs.common_functions import units_conversion, convert_temperature
from datetime import datetime
from UI.Comment import Comment
from UI.Transects2Use import Transects2Use
from UI.Options import Options
from UI.MagVar import MagVar
from UI.HOffset import HOffset
from UI.HSource import HSource
from UI.SOSSource import SOSSource
from UI.TempSource import TempSource
from UI.Salinity import Salinity
from UI.ShipTrack import Shiptrack
from UI.BoatSpeed import BoatSpeed
from UI.StationaryGraphs import StationaryGraphs
from UI.MplCanvas import MplCanvas
from contextlib import contextmanager
import time
import os


class QRev(QtWidgets.QMainWindow, QRev_gui.Ui_MainWindow):
    handle_args_trigger = pyqtSignal()
    gui_initialized = False
    command_arg = ""

    def __init__(self, parent=None, groupings=None, data=None, caller=None):
        super(QRev, self).__init__(parent)
        self.setupUi(self)

        self.QRev_version = 'QRevPy Beta'
        self.setWindowTitle(self.QRev_version)

        self.settingsFile = 'QRev_Settings'
        self.units = units_conversion(units_id='English')
        self.save_all = True
        self.change = False
        self.current_tab = 0
        # self.settings = SSet(self.settingsFile)

        self.actionOpen.triggered.connect(self.select_measurement)
        self.actionComment.triggered.connect(self.addComment)
        self.actionCheck.triggered.connect(self.selectTransects)
        self.actionBT.triggered.connect(self.setRef2BT)
        self.actionGGA.triggered.connect(self.setRef2GGA)
        self.actionVTG.triggered.connect(self.setRef2VTG)
        self.actionOFF.triggered.connect(self.compTracksOff)
        self.actionON.triggered.connect(self.compTracksOn)
        self.actionOptions.triggered.connect(self.qrev_options)
        self.tab_all.currentChanged.connect(self.tab_manager)

        self.font_bold = QtGui.QFont()
        self.font_bold.setBold(True)
        self.font_normal = QtGui.QFont()
        self.font_normal.setBold(False)

        self.icon_caution = QtGui.QIcon()
        self.icon_caution.addPixmap(QtGui.QPixmap(":/images/24x24/Warning.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.icon_warning = QtGui.QIcon()
        self.icon_warning.addPixmap(QtGui.QPixmap(":/images/24x24/Alert.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.icon_good = QtGui.QIcon()
        self.icon_good.addPixmap(QtGui.QPixmap(":/images/24x24/Yes.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.icon_allChecked = QtGui.QIcon()
        self.icon_allChecked.addPixmap(QtGui.QPixmap(":/images/24x24/Apply.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.icon_unChecked = QtGui.QIcon()
        self.icon_unChecked.addPixmap(QtGui.QPixmap(":/images/24x24/Warning.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.actionSave.setDisabled(True)
        self.actionComment.setDisabled(True)
        self.actionEDI.setDisabled(True)
        self.actionCheck.setDisabled(True)


        if QtCore.QSysInfo.windowsVersion() == QtCore.QSysInfo.WV_WINDOWS10:
            self.setStyleSheet(
                "QHeaderView::section{"
                "border-top: 0px solid #D8D8D8;"
                "border-left: 0px solid #D8D8D8;"
                "border-right: 1px solid #D8D8D8;"
                "border-bottom: 1px solid #D8D8D8;"
                "background-color: white;"
                "padding:4px;"
                "}"
                "QTableCornerButton::section{"
                "border-top: 0px solid #D8D8D8;"
                "border-left: 0px solid #D8D8D8;"
                "border-right: 1px solid #D8D8D8;"
                "border-bottom: 1px solid #D8D8D8;"
                "background-color: white;"
                "}")

        self.gui_initialized = True

        if caller is not None:
            self.caller = caller
            self.split_initialization(groupings=groupings, data=data)
            self.actionSave.triggered.connect(self.split_save)
            self.processed_data = []
        else:
            self.actionSave.triggered.connect(self.save_measurement)

# Toolbar functions
# =================
    def select_measurement(self):
        """Opens a dialog to allow the user to load measurement file(s) for viewing or processing.
        """

        # Open dialog
        self.select = OpenMeasurementDialog(self)
        self.select.exec_()

        # If a selection is made begin loading
        if len(self.select.type) > 0:
            # wait_cursor doesn't seem to be working properly
            with self.wait_cursor():
                # Load and process measurement based on measurement type
                if self.select.type == 'SonTek':
                    # Show folder name in GUI header
                    self.setWindowTitle(self.QRev_version + ': ' + self.select.pathName)
                    # Create measurement object
                    self.meas = Measurement(in_file=self.select.fullName, source='SonTek', proc_type='QRev')

                elif self.select.type == 'TRDI':
                    # Show mmt filename in GUI header
                    self.setWindowTitle(self.QRev_version + ': ' + self.select.fullName[0])
                    # Create measurement object
                    self.meas = Measurement(in_file=self.select.fullName[0], source='TRDI', proc_type='QRev', checked=self.select.checked)

                    # self.msg.destroy()
                elif self.select.type == 'QRev':
                    # Show QRev filename in GUI header
                    self.setWindowTitle(self.QRev_version + ': ' + self.select.fullName[0])
                    self.meas = Measurement(in_file=self.select.fullName, source='QRev')
                else:
                    print('Cancel')

                self.checked_transects_idx = Measurement.checked_transects(self.meas)
                self.h_external_valid = Measurement.h_external_valid(self.meas)
                self.actionSave.setEnabled(True)
                self.actionComment.setEnabled(True)
                self.change = True
                self.tab_manager(tab_idx=0)

    def save_measurement(self):
        """Save measurement in Matlab format.
        """
        # Create default file name
        save_file = SaveMeasurementDialog()

        # Save data in Matlab format
        if self.save_all:
            Python2Matlab.save_matlab_file(self.meas, save_file.full_Name)
        else:
            Python2Matlab.save_matlab_file(self.meas, save_file.full_Name, checked=self.checked_transects_idx)

    def addComment(self):
        """Add comment triggered by actionComment
        """
        # Intialize comment dialog
        self.comment = Comment(self)
        comment_entered = self.comment.exec_()

        # If comment entered and measurement open, save comment, and update comments tab.
        if comment_entered:
            if hasattr(self, 'meas'):
                self.meas.comments.append(self.comment.text_edit_comment.toPlainText())
            self.change = True
            self.tab_manager()

    def selectTransects(self):
        """Initializes a dialog to allow user to select or deselect transects to include in the measurement.
        """

        # Open dialog
        self.transects_2_use = Transects2Use(self)
        transects_selected = self.transects_2_use.exec_()
        selected_transects = []

        # Identify currently selected transects
        if transects_selected:
            with self.wait_cursor():
                for row in range(self.transects_2_use.tableSelect.rowCount()):
                    if self.transects_2_use.tableSelect.item(row, 0).checkState() == QtCore.Qt.Checked:
                        selected_transects.append(row)

                # Store selected transect indices
                self.checked_transects_idx = selected_transects

                # Update measurement based on the currently selected transects
                Measurement.selected_transects_changed(self.meas, self.checked_transects_idx)

                # Update the transect select icon on the toolbar
                self.update_toolbar_trans_select()

                # Update display
                self.change = True
                self.tab_manager()

    def setRef2BT(self):
        """Changes the navigation reference to Bottom Track
        """
        with self.wait_cursor():
            settings = Measurement.current_settings(self.meas)
            settings['NavRef'] = 'BT'
            Measurement.apply_settings(self.meas, settings)
            self.update_toolbar_nav_ref()
            self.change = True
            self.tab_manager()

    def setRef2GGA(self):
        """Changes the navigation reference to GPS GGA
        """
        with self.wait_cursor():
            settings = Measurement.current_settings(self.meas)
            settings['NavRef'] = 'GGA'
            Measurement.apply_settings(self.meas, settings)
            self.update_toolbar_nav_ref()
            self.change = True
            self.tab_manager()

    def setRef2VTG(self):
        """Changes the navigation reference to GPS VTG
        """
        with self.wait_cursor():
            settings = Measurement.current_settings(self.meas)
            settings['NavRef'] = 'VTG'
            Measurement.apply_settings(self.meas, settings)
            self.update_toolbar_nav_ref()
            self.change = True
            self.tab_manager()

    def compTracksOn(self):
        """Change composite tracks setting to On and update measurement and display.
        """
        with self.wait_cursor():
            settings = Measurement.current_settings(self.meas)
            settings['CompTracks'] = 'On'
            Measurement.apply_settings(self.meas, settings)
            self.update_toolbar_composite_tracks()
            self.change = True
            self.tab_manager()

    def compTracksOff(self):
        """Change composite tracks setting to Off and update measurement and display.
        """
        with self.wait_cursor():
            settings = Measurement.current_settings(self.meas)
            settings['CompTracks'] = 'Off'
            Measurement.apply_settings(self.meas, settings)
            self.update_toolbar_composite_tracks()
            self.change = True
            self.tab_manager()

    def qrev_options(self):
        """Change options triggered by actionOptions
                """
        # Intialize options dialog
        self.options = Options(self)
        selected_options = self.options.exec_()
        with self.wait_cursor():
            if self.options.rb_english.isChecked():
                if self.units['ID'] == 'SI':
                    self.units = units_conversion(units_id='English')
                    self.update_main()
                    self.change = True
            else:
                if self.units['ID'] == 'English':
                    self.units = units_conversion(units_id='SI')
                    self.update_main()
                    self.change = True

            if self.options.rb_All.isChecked():
                self.save_all = True
            else:
                self.save_all = False

            if self.options.cb_stylesheet.isChecked():
                self.save_stylesheet = True
            else:
                self.save_all = False

            self.tab_manager()

# Main tab
# ========
    def update_main(self):
        """Update Gui
        """
        with self.wait_cursor():
            # Update the transect select icon on the toolbar
            self.update_toolbar_trans_select()

            # Set toolbar navigation reference
            self.update_toolbar_nav_ref()

            # Set toolbar composite tracks indicator
            self.update_toolbar_composite_tracks()


            self.main_summary_table()
            self.uncertainty_table()
            self.qa_table()
            self.contour_shiptrack(self.checked_transects_idx[0])
            self.extrap_plot()
            self.discharge_plot()
            self.messages_tab()
            self.comments_tab()
            self.main_details_table()
            self.main_premeasurement_table()
            self.main_settings_table()
            self.main_adcp_table()
            self.change = False
            print('complete')

    def update_toolbar_trans_select(self):
        """Updates the icon for the select transects on the toolbar.
        """
        self.actionCheck.setEnabled(True)

        if len(self.checked_transects_idx) == len(self.meas.transects):
            self.actionCheck.setIcon(self.icon_allChecked)
        else:
            self.actionCheck.setIcon(self.icon_unChecked)

    def update_toolbar_composite_tracks(self):
        """Updates the toolbar to reflect the current setting for composite tracks.
        """
        # Set toolbar composite tracks indicator fonts
        font_bold = QtGui.QFont()
        font_bold.setBold(True)
        font_bold.setPointSize(11)

        font_normal = QtGui.QFont()
        font_normal.setBold(False)
        font_normal.setPointSize(11)

        # Set selection to bold
        if self.meas.transects[self.checked_transects_idx[0]].boat_vel.composite == 'On':
            self.actionON.setFont(font_bold)
            self.actionOFF.setFont(font_normal)
        else:
            self.actionON.setFont(font_normal)
            self.actionOFF.setFont(font_bold)

    def update_toolbar_nav_ref(self):
        """Update the display of the navigation reference on the toolbar.
        """
        # Get setting
        selected = self.meas.transects[self.checked_transects_idx[0]].boat_vel.selected

        # Set toolbar navigation indicator fonts
        font_bold = QtGui.QFont()
        font_bold.setBold(True)
        font_bold.setPointSize(11)

        font_normal = QtGui.QFont()
        font_normal.setBold(False)
        font_normal.setPointSize(11)

        # Bold the selected reference only
        if selected == 'bt_vel':
            self.actionBT.setFont(font_bold)
            self.actionGGA.setFont(font_normal)
            self.actionVTG.setFont(font_normal)
        elif selected == 'gga_vel':
            self.actionBT.setFont(font_normal)
            self.actionGGA.setFont(font_bold)
            self.actionVTG.setFont(font_normal)
        elif selected == 'vtg_vel':
            self.actionBT.setFont(font_normal)
            self.actionGGA.setFont(font_normal)
            self.actionVTG.setFont(font_bold)

    def uncertainty_table(self):
        """Create and populate uncertainty table.
        """
        # Setup table
        tbl = self.table_uncertainty
        tbl.clear()
        col_header = [self.tr('Uncertainty'), self.tr('Auto'), self.tr('  User  ')]
        ncols = len(col_header)
        nrows = 7
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(col_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.itemChanged.connect(self.recompute_uncertainty)
        tbl.itemChanged.disconnect()

        # Add labels and data
        row = 0
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem('Random 95%'))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.cov_95)))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        if self.meas.uncertainty.cov_95_user is not None:
            tbl.setItem(row, 2, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.cov_95_user)))

        row = row + 1
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr('Invalid Data 95%')))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.invalid_95)))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        if self.meas.uncertainty.cov_95_user is not None:
            tbl.setItem(row, 2, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.invalid_95_user)))

        row = row + 1
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr('Edge Q 95%')))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.edges_95)))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        if self.meas.uncertainty.cov_95_user is not None:
            tbl.setItem(row, 2, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.edges_95_user)))

        row = row + 1
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr('Extrapolation 95%')))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.extrapolation_95)))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        if self.meas.uncertainty.cov_95_user is not None:
            tbl.setItem(row, 2,
                        QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.extrapolation_95_user)))

        row = row + 1
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr('Moving-Bed 95%')))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.moving_bed_95)))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        if self.meas.uncertainty.cov_95_user is not None:
            tbl.setItem(row, 2, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.moving_bed_95_user)))

        row = row + 1
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr('Systematic 68%')))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.systematic)))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        if self.meas.uncertainty.cov_95_user is not None:
            tbl.setItem(row, 2, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.systematic_user)))

        row = row + 1
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr('Estimated 95%')))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 0).setFont(self.font_bold)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.total_95)))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 1).setFont(self.font_bold)
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.total_95_user)))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 2).setFont(self.font_bold)
        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        tbl.itemChanged.connect(self.recompute_uncertainty)

    def recompute_uncertainty(self):
        """Recomputes the uncertainty based on user input.
        """

        # Get edited value from table
        with self.wait_cursor():
            new_value = self.table_uncertainty.selectedItems()[0].text()
            if new_value == '':
                new_value = None
            else:
                new_value = float(new_value)

            # Identify uncertainty variable that was edited.
            row_index = self.table_uncertainty.selectedItems()[0].row()
            if row_index == 0:
                self.meas.uncertainty.cov_95_user = new_value
            elif row_index == 1:
                self.meas.uncertainty.invalid_95_user = new_value
            elif row_index == 2:
                self.meas.uncertainty.edges_95_user = new_value
            elif row_index == 3:
                self.meas.uncertainty.extrapolation_95_user = new_value
            elif row_index == 4:
                self.meas.uncertainty.moving_bed_95_user = new_value
            elif row_index == 5:
                self.meas.uncertainty.systematic_user = new_value

            # Compute new uncertainty values
            self.meas.uncertainty.estimate_total_uncertainty()

            # Update table
            if new_value is not None:
                self.table_uncertainty.item(row_index, 2).setText('{:8.1f}'.format(new_value))
            self.table_uncertainty.item(6, 2).setText('{:8.1f}'.format(self.meas.uncertainty.total_95_user))

    def qa_table(self):
        """Create and popluate quality assurance table.
        """
        # Setup table
        tbl = self.table_qa
        header = ['', self.tr('COV %'), '', self.tr('% Q')]
        ncols = len(header)
        nrows = 3
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Compute measurement properties
        trans_prop = self.meas.compute_measurement_properties(self.meas)
        discharge = self.meas.mean_discharges(self.meas)

        # Populate table
        row = 0
        # Discharge COV
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr('Q:')))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 0).setFont(self.font_bold)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('{:5.2f}'.format(self.meas.uncertainty.cov)))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Left and right edge % Q
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(self.tr('L/R Edge:')))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 2).setFont(self.font_bold)
        left = (discharge['left_mean'] / discharge['total_mean']) * 100
        right = (discharge['right_mean'] / discharge['total_mean']) * 100
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem('{:5.2f} / {:5.2f}'.format(left, right)))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        row = row + 1
        # Width COV
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr('Width:')))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 0).setFont(self.font_bold)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('{:5.2f}'.format(trans_prop['width_cov'][-1])))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Invalid cells
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(self.tr('Invalid Cells:')))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 2).setFont(self.font_bold)
        value = (discharge['int_cells_mean'] / discharge['total_mean']) * 100
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem('{:5.2f}'.format(value)))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        row = row + 1
        # Area COV
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr('Area:')))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 0).setFont(self.font_bold)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('{:5.2f}'.format(trans_prop['area_cov'][-1])))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Invalid ensembles
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(self.tr('Invalid Ens:')))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 2).setFont(self.font_bold)
        value = (discharge['int_ensembles_mean'] / discharge['total_mean']) * 100
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem('{:5.2f}'.format(value)))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def select_transect(self, row, column):
        """Update contour and shiptrack plots based on transect selected in main_summary_table.
        """

        # Transect column was selected
        if column == 0 and row > 0:
            with self.wait_cursor():
                # Set all files to normal font
                nrows = len(self.checked_transects_idx)
                for nrow in range(1, nrows+1):
                    self.main_table_summary.item(nrow, 0).setFont(self.font_normal)
                    self.main_table_details.item(nrow, 0).setFont(self.font_normal)
                    self.table_settings.item(nrow + 2, 0).setFont(self.font_normal)
                # Set selected file to bold font
                self.main_table_summary.item(row, 0).setFont(self.font_bold)
                self.main_table_details.item(row, 0).setFont(self.font_bold)
                self.table_settings.item(row + 2, 0).setFont(self.font_bold)
                # Determine transect selected
                transect_id = self.checked_transects_idx[row-1]
                # Update contour and shiptrack plot
                self.contour_shiptrack(transect_id=transect_id)

    def contour_shiptrack(self, transect_id=0):
        """Generates the color contour and shiptrack plot for the main tab.

        Parameters
        ----------
        transect_id: int
            Index to check transects to identify the transect to be plotted
        """

        # Assign layout to widget to allow auto scaling
        layout = QtWidgets.QVBoxLayout(self.graphics_main_middle)
        # Adjust margins of layout to maximize graphic area
        layout.setContentsMargins(1, 1, 1, 1)

        # Get transect data to be plotted
        transect = self.meas.transects[transect_id]

        # If figure already exists update it. If not, create it.
        if hasattr(self, 'middle_mpl'):
            self.middle_mpl.fig.clear()
            self.middle_mpl.contour_shiptrack(transect=transect, units=self.units)
        else:
            self.middle_mpl = Qtmpl(self.graphics_main_middle, width=15, height=1, dpi=80)
            self.middle_mpl.contour_shiptrack(transect=transect, units=self.units)
            layout.addWidget(self.middle_mpl)

        # Draw canvas
        self.middle_mpl.draw()

    def extrap_plot(self):
        """Generates the color contour and shiptrack plot for the main tab.
        """

        # Assign layout to widget to allow auto scaling
        layout = QtWidgets.QVBoxLayout(self.graphics_main_extrap)
        # Adjust margins of layout to maximize graphic area
        layout.setContentsMargins(1, 1, 1, 1)

        # If figure already exists update it. If not, create it.
        if hasattr(self, 'extrap_mpl'):
            self.extrap_mpl.fig.clear()
            self.extrap_mpl.extrap_plot(meas=self.meas)
        else:
            self.extrap_mpl = Qtmpl(self.graphics_main_extrap, width=1, height=4, dpi=80)
            self.extrap_mpl.extrap_plot(meas=self.meas)
            layout.addWidget(self.extrap_mpl)

        # Draw canvas
        self.extrap_mpl.draw()

    def discharge_plot(self):
        """Generates the color contour and shiptrack plot for the main tab.
        """

        # Assign layout to widget to allow auto scaling
        layout = QtWidgets.QVBoxLayout(self.graphics_main_timeseries)
        # Adjust margins of layout to maximize graphic area
        layout.setContentsMargins(1, 1, 1, 1)

        # If figure already exists update it. If not, create it.
        if hasattr(self, 'discharge_mpl'):
            self.discharge_mpl.fig.clear()
            self.discharge_mpl.discharge_plot(meas=self.meas, checked=self.checked_transects_idx,units=self.units)
        else:
            self.discharge_mpl = Qtmpl(self.graphics_main_timeseries, width=4, height=2, dpi=80)
            self.discharge_mpl.discharge_plot(meas=self.meas, checked=self.checked_transects_idx, units=self.units)
            layout.addWidget(self.discharge_mpl)

        # Draw canvas
        self.discharge_mpl.draw()

    def messages_tab(self):
        """Update messages tab.
        """

        # Initialize local variables
        qa = self.meas.qa
        tbl = self.main_message_table
        tbl.clear()
        main_message_header = [self.tr('Status'), self.tr('Message')]
        qa_check_keys = ['bt_vel', 'compass', 'depths', 'edges', 'extrapolation', 'gga_vel', 'moving_bed', 'system_tst',
                         'temperature', 'transects', 'user', 'vtg_vel', 'w_vel']

        # For each qa check retrieve messages and set tab icon based on the status
        messages = []
        for key in qa_check_keys:
            qa_type = getattr(qa, key)
            if qa_type['messages']:
                for message in qa_type['messages']:
                    messages.append(message)
            self.setIcon(key, qa_type['status'])

        # Sort messages with warning at top
        messages.sort(key=lambda x: x[1])

        # Setup table
        tbl = self.main_message_table
        main_message_header = [self.tr('Status'), self.tr('Message')]
        ncols = len(main_message_header)
        nrows = len(messages)
        tbl.setRowCount(nrows + 1)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(main_message_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Populate table
        for row, message in enumerate(messages):
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(message[0]))
            if message[1] == 1:
                tbl.item(row, 1).setFont(self.font_bold)
                item_warning = QtWidgets.QTableWidgetItem(self.icon_warning, '')
                tbl.setItem(row, 0, item_warning)
            else:
                item_caution = QtWidgets.QTableWidgetItem(self.icon_caution, '')
                tbl.setItem(row, 0, item_caution)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def setIcon(self, key, status):
        """Set tab icon based on qa check status.
        """

        # Identify tab name based on key
        if key == 'bt_vel':
            tab = 'tab_bt'
        elif key == 'compass':
            tab = 'tab_compass'
        elif key == 'depths':
            tab = 'tab_depth'
        elif key == 'edges':
            tab = 'tab_edges'
        elif key == 'extrapolation':
            tab = 'tab_extrap'
        elif key == 'gga_vel' or key == 'vtg_vel':
            gga_status = self.meas.qa.gga_vel['status']
            vtg_status = self.meas.qa.vtg_vel['status']
            status = 'good'
            if gga_status == 'caution' or vtg_status == 'caution':
                status = 'caution'
            if gga_status == 'warning' or vtg_status == 'warning':
                status = 'warning'
            tab = 'tab_gps'
        elif key == 'moving_bed':
            tab = 'tab_mbt'
        elif key == 'system_tst':
            tab = 'tab_systest'
        elif key == 'temperature':
            tab = 'tab_tempsal'
        elif key == 'transects' or 'user':
            tab = 'tab_main'
            transects_status = self.meas.qa.transects['status']
            user_status = self.meas.qa.user['status']
            status = 'good'
            if transects_status == 'caution' or user_status == 'caution':
                status = 'caution'
            if transects_status == 'warning' or user_status == 'warning':
                status = 'warning'
        elif key == 'w_vel':
            tab = 'tab_wt'

        # Set appropriate icon
        if status == 'good':
            self.tab_all.setTabIcon(self.tab_all.indexOf(self.tab_all.findChild(QtWidgets.QWidget, tab)),
                                    self.icon_good)
        elif status == 'caution':
            self.tab_all.setTabIcon(self.tab_all.indexOf(self.tab_all.findChild(QtWidgets.QWidget, tab)),
                                    self.icon_caution)
        elif status == 'warning':
            self.tab_all.setTabIcon(self.tab_all.indexOf(self.tab_all.findChild(QtWidgets.QWidget, tab)),
                                    self.icon_warning)
        self.tab_all.setIconSize(QtCore.QSize(15, 15))

    def comments_tab(self):
        """Display comments in comments tab.
        """
        self.display_comments.clear()
        if hasattr(self, 'meas'):
            self.display_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                # Display each comment on a new line
                self.display_comments.textCursor().insertText(comment)
                self.display_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_comments.textCursor().insertBlock()

# Main summary tabs
# =================
    def main_summary_table(self):
        """Create and populate main summary table.
        """

        # Setup table
        tbl = self.main_table_summary
        summary_header = [self.tr('Transect'), self.tr('Start'), self.tr('Bank'), self.tr('End'),
                               self.tr('Duration'), self.tr('Total Q'), self.tr('Top Q'), self.tr('Meas Q'),
                               self.tr('Bottom Q'), self.tr('Left Q'), self.tr('Right Q')]
        ncols = len(summary_header)
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows + 1)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(summary_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.cellClicked.connect(self.select_transect)

        # Add transect data
        for row in range(nrows):
            col = 0
            transect_id = self.checked_transects_idx[row]

            # File/transect name
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].file_name[:-4]))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect start time
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.fromtimestamp(
                self.meas.transects[transect_id].date_time.start_serial_time), '%H:%M:%S')))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect start edge
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].start_edge[0]))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect end time
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.fromtimestamp(
                self.meas.transects[transect_id].date_time.end_serial_time), '%H:%M:%S')))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect duration
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:5.1f}'.format(
                self.meas.transects[transect_id].date_time.transect_duration_sec)))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect total discharge
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:8.2f}'.format(self.meas.discharge[transect_id].total
                                                                                  * self.units['Q'])))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect top discharge
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[transect_id].top
                                                                                  * self.units['Q'])))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect middle discharge
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[transect_id].middle
                                                                                  * self.units['Q'])))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect bottom discharge
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[transect_id].bottom
                                                                                  * self.units['Q'])))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect left discharge
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[transect_id].left
                                                                                  * self.units['Q'])))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect right discharge
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[transect_id].right
                                                                                  * self.units['Q'])))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Add measurement summaries

        # Row label
        col = 0
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(self.tr('Measurement')))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Measurement start time
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(tbl.item(1, col).text()))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Skip start bank
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(''))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Measurement end time
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(tbl.item(nrows, col).text()))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Measurement duration
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:5.1f}'.format(Measurement.measurement_duration(self.meas))))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Mean total discharge
        discharge = Measurement.mean_discharges(self.meas)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:8.2f}'.format(discharge['total_mean'] * self.units['Q'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Mean top discharge
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(discharge['top_mean'] * self.units['Q'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Mean middle discharge
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(discharge['mid_mean'] * self.units['Q'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Mean bottom discharge
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(discharge['bot_mean'] * self.units['Q'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Mean left discharge
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(discharge['left_mean'] * self.units['Q'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Mean right discharge
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(discharge['right_mean'] * self.units['Q'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Bold Measurement row
        for col in range(ncols):
            tbl.item(0, col).setFont(self.font_bold)

        tbl.item(1, 0).setFont(self.font_bold)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def main_details_table(self):
        """Initialize and populate the details table.
        """

        # Setup table
        tbl = self.main_table_details
        summary_header = [self.tr('Transect'),
                          self.tr('Width' + '\n ' + self.units['label_L']),
                          self.tr('Area' + '\n ' + self.units['label_A']),
                          self.tr('Avg Boat \n Speed' + ' ' + self.units['label_V']),
                          self.tr('Course Made \n Good' + ' (deg)'),
                          self.tr('Q/A' + ' ' + self.units['label_V']),
                          self.tr('Avg Water \n Direction' + ' (deg)')]
        ncols = len(summary_header)
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows + 1)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(summary_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.cellClicked.connect(self.select_transect)

        trans_prop = Measurement.compute_measurement_properties(self.meas)

        # Add transect data
        for row in range(nrows):
            col = 0
            transect_id = self.checked_transects_idx[row]

            # File/transect name
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].file_name[:-4]))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect width
            col += 1
            item = '{:10.2f}'.format(trans_prop['width'][transect_id])
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect area
            col += 1
            item = '{:10.2f}'.format(trans_prop['area'][transect_id])
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect average boat speed
            col += 1
            item = '{:6.2f}'.format(trans_prop['avg_boat_speed'][transect_id])
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect average boat course
            col += 1
            item = '{:6.2f}'.format(trans_prop['avg_boat_course'][transect_id])
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect average water speed
            col += 1
            item = '{:6.2f}'.format(trans_prop['avg_water_speed'][transect_id])
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect average water direction
            col += 1
            item = '{:6.2f}'.format(trans_prop['avg_water_dir'][transect_id])
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Add measurement summaries
        n_transects = len(self.meas.transects)
        col = 0

        # Row label
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(self.tr('Average')))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Average width
        col += 1
        item = '{:10.2f}'.format(trans_prop['width'][n_transects])
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Average area
        col += 1
        item = '{:10.2f}'.format(trans_prop['area'][n_transects])
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Average boat speed
        col += 1
        item = '{:6.2f}'.format(trans_prop['avg_boat_speed'][n_transects])
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Skip average boat course
        col += 1

        # Average water speed
        col += 1
        item = '{:6.2f}'.format(trans_prop['avg_water_speed'][n_transects])
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Average water direction
        col += 1
        item = '{:6.2f}'.format(trans_prop['avg_water_dir'][n_transects])
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Set average row font to bold
        for col in range(ncols):
            if col != 4:
                tbl.item(0, col).setFont(self.font_bold)

        tbl.item(1, 0).setFont(self.font_bold)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def main_premeasurement_table(self):
        """Initialize and populate the premeasurement table.
        """

        # Initialize and connect the station name and number fields
        self.ed_site_name.setText(self.meas.station_name)
        self.ed_site_number.setText(self.meas.station_number)
        self.ed_site_name.editingFinished.connect(self.update_site_name)
        self.ed_site_number.editingFinished.connect(self.update_site_number)

        # Setup table
        tbl = self.table_premeas
        ncols = 4
        nrows = 5
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.horizontalHeader().hide()
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # ADCP Test
        tbl.setItem(0, 0, QtWidgets.QTableWidgetItem(self.tr('ADCP Test: ')))
        tbl.item(0, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(0, 0).setFont(self.font_bold)
        # Determine is a system test was recorded
        if not self.meas.system_tst:
            tbl.setItem(0, 1, QtWidgets.QTableWidgetItem(self.tr('No')))
        else:
            tbl.setItem(0, 1, QtWidgets.QTableWidgetItem(self.tr('Yes')))
        tbl.item(0, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Report test fails
        tbl.setItem(0, 2, QtWidgets.QTableWidgetItem(self.tr('ADCP Test Fails: ')))
        tbl.item(0, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(0, 2).setFont(self.font_bold)
        num_tests_with_failure = 0
        for test in self.meas.system_tst:
            if hasattr(test, 'result'):
                if test.result['n_failed'] is not None and test.result['n_failed'] > 0:
                    num_tests_with_failure += 1
        tbl.setItem(0, 3, QtWidgets.QTableWidgetItem('{:2.0f}'.format(num_tests_with_failure)))
        tbl.item(0, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Compass Calibration
        tbl.setItem(1, 0, QtWidgets.QTableWidgetItem(self.tr('Compass Calibration: ')))
        tbl.item(1, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(1, 0).setFont(self.font_bold)
        if not self.meas.compass_cal:
            tbl.setItem(1, 1, QtWidgets.QTableWidgetItem(self.tr('No')))
        else:
            tbl.setItem(1, 1, QtWidgets.QTableWidgetItem(self.tr('Yes')))
        tbl.item(1, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Compass Evaluation
        tbl.setItem(1, 2, QtWidgets.QTableWidgetItem(self.tr('Compass Evaluation: ')))
        tbl.item(1, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(1, 2).setFont(self.font_bold)
        if not self.meas.compass_eval:
            tbl.setItem(1, 3, QtWidgets.QTableWidgetItem(self.tr('No')))
        else:
            tbl.setItem(1, 3, QtWidgets.QTableWidgetItem('{:3.1f}'.format(self.meas.compass_cal[-1].result['compass']['error'])))
        tbl.item(1, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Moving-Bed Test
        tbl.setItem(2, 0, QtWidgets.QTableWidgetItem(self.tr('Moving-Bed Test: ')))
        tbl.item(2, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(2, 0).setFont(self.font_bold)
        if len(self.meas.mb_tests) < 1:
            tbl.setItem(2, 1, QtWidgets.QTableWidgetItem(self.tr('No')))
        else:
            tbl.setItem(2, 1, QtWidgets.QTableWidgetItem(self.tr('Yes')))
        tbl.item(2, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Report if the test indicated a moving bed
        tbl.setItem(2, 2, QtWidgets.QTableWidgetItem(self.tr('Moving-Bed?: ')))
        tbl.item(2, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(2, 2).setFont(self.font_bold)
        if len(self.meas.mb_tests) < 1:
            tbl.setItem(2, 3, QtWidgets.QTableWidgetItem(self.tr('Unknown')))
        else:
            moving_bed = 'No'
            for test in self.meas.mb_tests:
                if test.selected:
                    if test.moving_bed == 'Yes':
                        moving_bed = self.tr('Yes')
            tbl.setItem(2, 3, QtWidgets.QTableWidgetItem(moving_bed))
        tbl.item(2, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Independent Temperature
        tbl.setItem(3, 0, QtWidgets.QTableWidgetItem(self.tr('Independent Temperature (C): ')))
        tbl.item(3, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(3, 0).setFont(self.font_bold)
        if type(self.meas.ext_temp_chk['user']) != float:
            tbl.setItem(3, 1, QtWidgets.QTableWidgetItem(self.tr('N/A')))
        else:
            tbl.setItem(3, 1, QtWidgets.QTableWidgetItem('{:4.1f}'.format(self.meas.ext_temp_chk['user'])))
        tbl.item(3, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # ADCP temperature
        tbl.setItem(3, 2, QtWidgets.QTableWidgetItem(self.tr('ADCP Temperature (C): ')))
        tbl.item(3, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(3, 2).setFont(self.font_bold)
        if type(self.meas.ext_temp_chk['adcp']) != float:
            avg_temp = Sensors.avg_temperature(self.meas.transects)
            tbl.setItem(3, 3, QtWidgets.QTableWidgetItem('{:4.1f}'.format(avg_temp)))
        else:
            tbl.setItem(3, 3, QtWidgets.QTableWidgetItem('{:4.1f}'.format(self.meas.ext_temp_chk['adcp'])))
        tbl.item(3, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Magnetic variation
        tbl.setItem(4, 0, QtWidgets.QTableWidgetItem(self.tr('Magnetic Variation: ')))
        tbl.item(4, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(4, 0).setFont(self.font_bold)
        magvar = []
        for transect in self.meas.transects:
            if transect.checked:
                magvar.append(transect.sensors.heading_deg.internal.mag_var_deg)
        if len(np.unique(magvar)) > 1:
            tbl.setItem(4, 1, QtWidgets.QTableWidgetItem(self.tr('Varies')))
        else:
            tbl.setItem(4, 1, QtWidgets.QTableWidgetItem('{:4.1f}'.format(magvar[0])))
        tbl.item(4, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Heading offset
        tbl.setItem(4, 2, QtWidgets.QTableWidgetItem(self.tr('Heading Offset: ')))
        tbl.item(4, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(4, 2).setFont(self.font_bold)
        hoffset = []
        for transect in self.meas.transects:
            if transect.sensors.heading_deg.external is None:
                tbl.setItem(4, 3, QtWidgets.QTableWidgetItem(self.tr('N/A')))
            if transect.checked:
                hoffset.append(transect.sensors.heading_deg.internal.align_correction_deg)
        if len(np.unique(hoffset)) > 1:
            tbl.setItem(4, 3, QtWidgets.QTableWidgetItem(self.tr('Varies')))
        else:
            tbl.setItem(4, 3, QtWidgets.QTableWidgetItem('{:4.1f}'.format(hoffset[0])))
        tbl.item(4, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def update_site_name(self):
        """Sets the station name to the name entered by the user.
        """
        self.meas.station_name = self.ed_site_name.text()

    def update_site_number(self):
        """Sets the station number to the number entered by the user.
        """
        self.meas.station_number = self.ed_site_name.text()

    def main_settings_table(self):
        """Create and populate settings table.
        """

        # Setup table
        tbl = self.table_settings
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows + 3)
        tbl.setColumnCount(14)
        tbl.horizontalHeader().hide()
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.cellClicked.connect(self.settings_table_row_adjust)

        # Build column labels using custom_header to create appropriate spans
        self.custom_header(tbl, 0, 0, 3, 1, self.tr('Transect'))
        self.custom_header(tbl, 0, 1, 1, 4, self.tr('Edge'))
        tbl.item(0, 1).setTextAlignment(QtCore.Qt.AlignCenter)
        self.custom_header(tbl, 1, 1, 1, 2, self.tr('Distance ' + self.units['label_L']))
        tbl.item(1, 1).setTextAlignment(QtCore.Qt.AlignCenter)
        self.custom_header(tbl, 2, 1, 1, 1, self.tr('Left'))
        tbl.item(2, 1).setTextAlignment(QtCore.Qt.AlignCenter)
        self.custom_header(tbl, 2, 2, 1, 1, self.tr('Right'))
        tbl.item(2, 2).setTextAlignment(QtCore.Qt.AlignCenter)
        self.custom_header(tbl, 1, 3, 1, 2, self.tr('Type'))
        tbl.item(1, 3).setTextAlignment(QtCore.Qt.AlignCenter)
        self.custom_header(tbl, 2, 3, 1, 1, self.tr('Left'))
        self.custom_header(tbl, 2, 4, 1, 1, self.tr('Right'))
        self.custom_header(tbl, 0, 5, 3, 1, self.tr('Draft ' + self.units['label_L']))
        self.custom_header(tbl, 0, 6, 3, 1, self.tr('Excluded \n Distance ' + self.units['label_L']))
        self.custom_header(tbl, 0, 7, 2, 2, self.tr('Depth'))
        tbl.item(0, 7).setTextAlignment(QtCore.Qt.AlignCenter)
        self.custom_header(tbl, 1, 7, 1, 1, self.tr('Ref'))
        self.custom_header(tbl, 1, 8, 1, 1, self.tr('Comp'))
        self.custom_header(tbl, 0, 9, 2, 2, self.tr('Navigation'))
        tbl.item(0, 9).setTextAlignment(QtCore.Qt.AlignCenter)
        self.custom_header(tbl, 2, 9, 1, 1, self.tr('Ref'))
        self.custom_header(tbl, 2, 10, 1, 1, self.tr('Comp'))
        self.custom_header(tbl, 0, 11, 3, 1, self.tr('Top \n Method'))
        tbl.item(0, 11).setTextAlignment(QtCore.Qt.AlignCenter)
        self.custom_header(tbl, 0, 12, 3, 1, self.tr('Bottom \n Method'))
        tbl.item(0, 12).setTextAlignment(QtCore.Qt.AlignCenter)
        self.custom_header(tbl, 0, 13, 3, 1, self.tr('Exp'))
        tbl.item(0, 13).setTextAlignment(QtCore.Qt.AlignCenter)

        # Add transect data
        for row in range(nrows):
            col = 0
            transect_id = self.checked_transects_idx[row]

            # File/transect name
            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].file_name[:-4]))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Left edge distance
            col += 1
            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(
                '{:5.1f}'.format(self.meas.transects[transect_id].edges.left.distance_m * self.units['L'])))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Right edge distance
            col += 1
            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(
                '{:5.1f}'.format(self.meas.transects[transect_id].edges.right.distance_m * self.units['L'])))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Left edge type
            col += 1
            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(
                self.meas.transects[transect_id].edges.left.type[0:3]))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Right edge type
            col += 1
            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(
                self.meas.transects[transect_id].edges.right.type[0:3]))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Draft or transducer depth
            col += 1
            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(
                '{:5.2f}'.format(self.meas.transects[transect_id].depths.bt_depths.draft_use_m * self.units['L'])))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Excluded distance below transducer
            col += 1
            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(
                '{:4.2f}'.format(self.meas.transects[transect_id].w_vel.excluded_dist_m * self.units['L'])))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Selected depth reference
            col += 1
            if self.meas.transects[transect_id].depths.selected == 'bt_depths':
                item = 'BT'
            elif self.meas.transects[transect_id].depths.selected == 'ds_depths':
                item = 'DS'
            elif self.meas.transects[transect_id].depths.selected == 'vb_depths':
                item = 'VB'
            else:
                item = '?'
            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Use of composite depths
            col += 1
            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].depths.composite))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Navigation or velocity reference
            col += 1
            if self.meas.transects[transect_id].boat_vel.selected == 'bt_vel':
                item = 'BT'
            elif self.meas.transects[transect_id].boat_vel.selected == 'gga_vel':
                item = 'GGA'
            elif self.meas.transects[transect_id].boat_vel.selected == 'vtg_vel':
                item = 'VTG'
            else:
                item = '?'
            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Composite tracks setting
            col += 1
            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].boat_vel.composite))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Extrapolation top method
            col += 1
            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].extrap.top_method))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Extrapolation bottom method
            col += 1
            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].extrap.bot_method))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Extrapolation exponent
            col += 1
            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(
                '{:5.4f}'.format(self.meas.transects[transect_id].extrap.exponent)))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1

            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

            tbl.item(3, 0).setFont(self.font_bold)

    def settings_table_row_adjust(self, row, col):
        """Allows proper selection of transect to display from the settings table which has custom header rows.

        Parameter
        =========
        row: int
            row selected
        col: int
            column selected
        """
        row = row - 2
        self.select_transect(row, col)

    def main_adcp_table(self):
        """Display ADCP table.
        """

        # Setup table
        tbl = self.table_adcp
        tbl.setRowCount(4)
        tbl.setColumnCount(4)
        tbl.horizontalHeader().hide()
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Serial number
        tbl.setItem(0, 0, QtWidgets.QTableWidgetItem(self.tr('Serial Number: ')))
        tbl.item(0, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(0, 0).setFont(self.font_bold)
        # Get serial number from 1st checked transect
        tbl.setItem(0, 1, QtWidgets.QTableWidgetItem(
            self.meas.transects[self.checked_transects_idx[0]].adcp.serial_num))
        tbl.item(0, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Manufacturer
        tbl.setItem(0, 2, QtWidgets.QTableWidgetItem(self.tr('Manufacturer: ')))
        tbl.item(0, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(0, 2).setFont(self.font_bold)
        tbl.setItem(0, 3, QtWidgets.QTableWidgetItem(
            self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer))
        tbl.item(0, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Model
        tbl.setItem(1, 0, QtWidgets.QTableWidgetItem(self.tr('Model: ')))
        tbl.item(1, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(1, 0).setFont(self.font_bold)
        tbl.setItem(1, 1, QtWidgets.QTableWidgetItem(self.meas.transects[self.checked_transects_idx[0]].adcp.model))
        tbl.item(1, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Firmware
        tbl.setItem(1, 2, QtWidgets.QTableWidgetItem(self.tr('Firmware: ')))
        tbl.item(1, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(1, 2).setFont(self.font_bold)
        if type(self.meas.transects[self.checked_transects_idx[0]].adcp.firmware) == str:
            firmware = self.meas.transects[self.checked_transects_idx[0]].adcp.firmware
        else:
            firmware = str(self.meas.transects[self.checked_transects_idx[0]].adcp.firmware)
        tbl.setItem(1, 3, QtWidgets.QTableWidgetItem(firmware))
        tbl.item(1, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Frequency
        tbl.setItem(2, 0, QtWidgets.QTableWidgetItem(self.tr('Frequency (kHz): ')))
        tbl.item(2, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(2, 0).setFont(self.font_bold)
        if self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer == 'SonTek':
            item = 'Variable'
        else:
            item = '{:4.0f}'.format(self.meas.transects[self.checked_transects_idx[0]].adcp.frequency_khz)
        tbl.setItem(2, 1, QtWidgets.QTableWidgetItem(item))
        tbl.item(2, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Depth cell size
        tbl.setItem(2, 2, QtWidgets.QTableWidgetItem(self.tr('Depth Cell Size (cm): ')))
        tbl.item(2, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(2, 2).setFont(self.font_bold)
        # Check for and handle multiple cell sizes
        cell_sizes = np.array([])
        for n in range(len(self.checked_transects_idx)):
            transect = self.meas.transects[self.checked_transects_idx[n]]
            cell_sizes = np.append(cell_sizes, np.unique(transect.depths.bt_depths.depth_cell_size_m)[:])
        max_cell_size = np.nanmax(cell_sizes) * 100
        min_cell_size = np.nanmin(cell_sizes) * 100
        if max_cell_size - min_cell_size < 1:
            size = '{:3.0f}'.format(max_cell_size)
        else:
            size = '{:3.0f} - {:3.0f}'.format(min_cell_size, max_cell_size)
        tbl.setItem(2, 3, QtWidgets.QTableWidgetItem(size))
        tbl.item(2, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Water mode
        tbl.setItem(3, 0, QtWidgets.QTableWidgetItem(self.tr('Water Mode: ')))
        tbl.item(3, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(3, 0).setFont(self.font_bold)
        if self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer == 'SonTek':
            item = 'Variable'
        else:
            item = '{:2.0f}'.format(self.meas.transects[self.checked_transects_idx[0]].w_vel.water_mode)
        tbl.setItem(3, 1, QtWidgets.QTableWidgetItem(item))
        tbl.item(3, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Bottom mode
        tbl.setItem(3, 2, QtWidgets.QTableWidgetItem(self.tr('Bottom Mode: ')))
        tbl.item(3, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(3, 2).setFont(self.font_bold)
        if self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer == 'SonTek':
            item = 'Variable'
        else:
            item = '{:2.0f}'.format(self.meas.transects[self.checked_transects_idx[0]].boat_vel.bt_vel.bottom_mode)
        tbl.setItem(3, 3, QtWidgets.QTableWidgetItem(item))
        tbl.item(3, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def custom_header(self, tbl, row, col, row_span, col_span, text):
        """Creates custom header than can span multiple rows and columns.

        Parameters
        ==========
        tbl: QTableWidget
            Reference to table
        row: int
            Initial row
        col: int
            Initial column
        row_span: int
            Number of rows to span
        col_span:
            Number of columns to span
        text: str
            Header text"""
        tbl.setItem(row, col, QtWidgets.QTableWidgetItem(text))
        tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, col).setFont(self.font_bold)
        tbl.setSpan(row, col, row_span, col_span)
        tbl.setWordWrap(True)

# System test tab
# ===============
    def system_tab(self, idx_systest=0):
        """Initialize and display data in the systems tab.
        idx_systest: int
            Identifies the system test to display in the text box.
        """

        # Setup table
        tbl = self.table_systest
        nrows = len(self.meas.system_tst)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(4)
        header_text = [self.tr('Date/Time'), self.tr('No. Tests'), self.tr('No. Failed'), self.tr('PT3')]
        tbl.setHorizontalHeaderLabels(header_text)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.cellClicked.connect(self.select_systest)

        # Add system tests
        if nrows > 0:
            for row, test in enumerate(self.meas.system_tst):

                # Test identifier
                col = 0
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(test.time_stamp))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Number of subtests run
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:2.0f}'.format(test.result['n_tests'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Number of subtests failed
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:2.0f}'.format(test.result['n_failed'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Status of PT3 tests
                col += 1
                if len(self.meas.qa.system_tst['messages']) > 0:
                    if self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer == 'TRDI':
                        if any("PT3" in item for item in self.meas.qa.system_tst['messages']):
                            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('Failed'))
                        else:
                            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('Pass'))
                    else:
                        tbl.setItem(row, col, QtWidgets.QTableWidgetItem('N/A'))
                elif self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer == 'TRDI':
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem('Pass'))
                else:
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem('N/A'))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Display selected test
                tbl.item(idx_systest, 0).setFont(self.font_bold)
                self.display_systest.clear()
                self.display_systest.textCursor().insertText(self.meas.system_tst[idx_systest].data)

                tbl.resizeColumnsToContents()
                tbl.resizeRowsToContents()

        # Clear current contents
        self.display_systest_comments.clear()
        self.display_systest_messages.clear()
        if hasattr(self, 'meas'):

            # Comments
            self.display_systest_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                # Display each comment on a new line
                self.display_systest_comments.textCursor().insertText(comment)
                self.display_systest_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_systest_comments.textCursor().insertBlock()

            # Messages
            self.display_systest_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.system_tst['messages']:
                # Display each comment on a new line
                self.display_systest_messages.textCursor().insertText(message[0])
                self.display_systest_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_systest_messages.textCursor().insertBlock()

    def select_systest(self, row, column):
        """Displays selected system test in text box.

        Parameters
        ==========
        row: int
            row in table clicked by user
        column: int
            column in table clicked by user
        """

        tbl = self.table_systest
        if column == 0:
            with self.wait_cursor():
                # Set all files to normal font
                nrows = len(self.meas.system_test)
                for nrow in range(nrows):
                    self.self.table_systest(nrow, 0).setFont(self.font_normal)

                # Set selected file to bold font
                self.table_systest.item(row, 0).setFont(self.font_bold)

                # Update contour and shiptrack plot
                self.system_tab(idx_systest=row)

# Compass tab
# ===========
    def compass_tab(self):
        """Initialize, setup settings, and display initial data in compass tabs.
        """

        # Setup data table
        tbl = self.table_compass_pr
        table_header = [self.tr('Plot / Transect'),
                          self.tr('Magnetic \n Variation (deg)'),
                          self.tr('Heading \n Offset (deg)'),
                          self.tr('Heading \n Source'),
                          self.tr('Pitch \n Mean (deg)'),
                          self.tr('Pitch \n Std. Dev. (deg)'),
                          self.tr('Roll \n Mean (deg)'),
                          self.tr('Roll \n Std. Dev. (deg)'),
                          self.tr('Discharge \n Previous \n' + self.units['label_Q']),
                          self.tr('Discharge \n Now \n' + self.units['label_Q']),
                          self.tr('Discharge \n % Change')]
        ncols = len(table_header)
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.cellClicked.connect(self.compass_table_clicked)

        # Update table, graphs, messages, and comments
        self.update_compass_tab(tbl=tbl, old_discharge=self.meas.discharge,
                                new_discharge=self.meas.discharge, initial=0)

        # Connect plot variable checkboxes
        self.cb_adcp_compass.stateChanged.connect(self.compass_plot)
        self.cb_ext_compass.stateChanged.connect(self.compass_plot)
        self.cb_mag_field.stateChanged.connect(self.compass_plot)
        self.cb_pitch.stateChanged.connect(self.pr_plot)
        self.cb_roll.stateChanged.connect(self.pr_plot)
        for transect_idx in self.checked_transects_idx:
            if self.meas.transects[transect_idx].sensors.heading_deg.internal.mag_error is not None:
                self.cb_mag_field.setEnabled(True)
                break
        for transect_idx in self.checked_transects_idx:
            if self.meas.transects[transect_idx].sensors.heading_deg.external is not None:
                self.cb_ext_compass.setEnabled(True)
                break

        # Initialize the calibration/evaluation tab
        self.compass_cal_eval(idx_eval=0)

    def compass_cal_eval(self, idx_cal=None, idx_eval=None):
        """Displays data in the calibration / evaluation tab.

        idx_cal: int
            Index of calibration to display in text box
        idx_eval: int
            Index of evaluation to display in text box
        """

        # Setup calibration table
        tblc = self.table_compass_cal
        nrows = len(self.meas.compass_cal)
        tblc.setRowCount(nrows)
        tblc.setColumnCount(1)
        header_text = [self.tr('Date/Time')]
        tblc.setHorizontalHeaderLabels(header_text)
        tblc.horizontalHeader().setFont(self.font_bold)
        tblc.verticalHeader().hide()
        tblc.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tblc.cellClicked.connect(self.select_calibration)

        # Add calibrations
        if nrows > 0:
            for row, test in enumerate(self.meas.compass_cal):
                col = 0
                tblc.setItem(row, col, QtWidgets.QTableWidgetItem(test.time_stamp))
                tblc.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Display selected calibration in text box
            if idx_cal is not None:
                self.display_compass_result.clear()
                tblc.item(idx_cal, 0).setFont(self.font_bold)
                self.display_compass_result.textCursor().insertText(self.meas.compass_cal[idx_cal].data)

            tblc.resizeColumnsToContents()
            tblc.resizeRowsToContents()

        # Setup evaluation table
        tble = self.table_compass_eval

        # SonTek has no independent evaluation. Evaluation results are reported with the calibration.
        if self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer == 'SonTek':
            evals = self.meas.compass_cal
        else:
            evals = self.meas.compass_eval
        nrows = len(evals)
        tble.setRowCount(nrows)
        tble.setColumnCount(2)
        header_text = [self.tr('Date/Time'), self.tr('Error')]
        tble.setHorizontalHeaderLabels(header_text)
        tble.horizontalHeader().setFont(self.font_bold)
        tble.verticalHeader().hide()
        tble.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tble.cellClicked.connect(self.select_evaluation)

        # Add evaluations
        if nrows > 0:
            for row, test in enumerate(evals):
                col = 0
                tble.setItem(row, col, QtWidgets.QTableWidgetItem(test.time_stamp))
                tble.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                col = 1
                if type(test.result['compass']['error']) == str:
                    item = test.result['compass']['error']
                else:
                    item = '{:2.2f}'.format(test.result['compass']['error'])
                tble.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tble.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Display selected evaluation in text box
            if idx_eval is not None:
                self.display_compass_result.clear()
                tble.item(idx_eval, 0).setFont(self.font_bold)
                self.display_compass_result.textCursor().insertText(evals[idx_eval].data)

            tble.resizeColumnsToContents()
            tble.resizeRowsToContents()

    def compass_comments_messages(self):
        """Displays the messages associated with the compass, pitch, and roll and any comments provided by the user.
        """

        # Clear current content
        self.display_compass_comments.clear()
        self.display_compass_messages.clear()
        if hasattr(self, 'meas'):

            # Comments
            self.display_compass_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                # Display each comment on a new line
                self.display_compass_comments.textCursor().insertText(comment)
                self.display_compass_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_compass_comments.textCursor().insertBlock()

            # Messages
            self.display_compass_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.compass['messages']:
                # Display each comment on a new line
                self.display_compass_messages.textCursor().insertText(message[0])
                self.display_compass_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_compass_messages.textCursor().insertBlock()

    def update_compass_tab(self, tbl, old_discharge, new_discharge, initial=None):
        """Populates the table and draws the graphs with the current data.

        tbl: QTableWidget
            Reference to the QTableWidget
        old_discharge: object
            Object of class QComp with discharge from previous settings, same as new if not changes
        new_discharge: object
            Object of class QComp with discharge from current settings
        initial: int
            Identifies row that should be checked and displayed in the graphs. Used for initial display of data.
        """

        with self.wait_cursor():
            # Populate each row
            for row in range(tbl.rowCount()):
                transect_id = self.checked_transects_idx[row]

                # File/Transect name
                col = 0
                checked = QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].file_name[:-4])
                checked.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(checked))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Magnetic variation
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(
                    self.meas.transects[transect_id].sensors.heading_deg.internal.mag_var_deg)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Heading offset
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(
                    self.meas.transects[transect_id].sensors.heading_deg.internal.align_correction_deg)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Heading source
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(
                    self.meas.transects[transect_id].sensors.heading_deg.selected))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Mean pitch
                col += 1
                pitch = getattr(self.meas.transects[transect_id].sensors.pitch_deg,
                                self.meas.transects[transect_id].sensors.pitch_deg.selected)
                item = np.nanmean(pitch.data)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(item)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Pitch standard deviation
                col += 1
                item = np.nanstd(pitch.data, ddof=1)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(item)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Mean roll
                col += 1
                roll = getattr(self.meas.transects[transect_id].sensors.roll_deg,
                               self.meas.transects[transect_id].sensors.roll_deg.selected)
                item = np.nanmean(roll.data)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(item)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Roll standard deviation
                col += 1
                item = np.nanstd(roll.data, ddof=1)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(item)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge from previous settings
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(old_discharge[transect_id].total)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge from new/current settings
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(new_discharge[transect_id].total)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent difference in old and new discharges
                col += 1
                per_change = ((new_discharge[transect_id].total - old_discharge[transect_id].total)
                              / old_discharge[transect_id].total) * 100
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(per_change)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Automatically resize rows and columns
                tbl.resizeColumnsToContents()
                tbl.resizeRowsToContents()

                # If initial is specified uncheck all rows and check the row specified by initial
                if initial is not None:
                    tbl.item(row, 0).setCheckState(QtCore.Qt.Unchecked)
                    tbl.item(initial, 0).setCheckState(QtCore.Qt.Checked)

            # Update graphics, comments, and messages
            self.compass_plot()
            self.pr_plot()
            self.compass_comments_messages()

    def compass_table_clicked(self, row, column):
        """Manages actions caused by the user clicking in selected columns of the table.

        Parameters
        ==========
        row: int
            row in table clicked by user
        column: int
            column in table clicked by user
        """

        tbl = self.table_compass_pr

        # Change transects plotted
        if column == 0:
            if tbl.item(row, 0).checkState() == QtCore.Qt.Checked:
                tbl.item(row, 0).setCheckState(QtCore.Qt.Unchecked)
            else:
                tbl.item(row, 0).setCheckState(QtCore.Qt.Checked)
            self.compass_plot()
            self.pr_plot()

        # Magnetic variation
        if column == 1:
            # Intialize dialog
            magvar_dialog = MagVar(self)
            magvar_entered = magvar_dialog.exec_()
            # Data entered.
            with self.wait_cursor():
                if magvar_entered:
                    old_discharge = self.meas.discharge
                    magvar = float(magvar_dialog.ed_magvar.text())

                    # Apply change to selected or all transects
                    if magvar_dialog.rb_all.isChecked():
                        self.meas.change_magvar(magvar=magvar)
                    else:
                        self.meas.change_magvar( magvar=magvar, transect_idx=self.transects_2_use[row])

                    # Update compass tab
                    self.update_compass_tab(tbl=tbl, old_discharge=old_discharge, new_discharge=self.meas.discharge)

        # Heading Offset
        elif column == 2:
            if self.h_external_valid:
                # Intialize dialog
                h_offset_dialog = HOffset(self)
                h_offset_entered = h_offset_dialog.exec_()
                # If data entered.
                with self.wait_cursor():
                    if h_offset_entered:
                        old_discharge = self.meas.discharge
                        h_offset = float(h_offset_dialog.ed_hoffset.text())

                        # Apply change to selected or all transects
                        if h_offset_dialog.rb_all.isChecked():
                            self.meas.change_h_offset(h_offset=h_offset)
                        else:
                            self.meas.change_h_offset(h_offset=h_offset, transect_idx=self.transects_2_use[row])

                        # Update compass tab
                        self.update_compass_tab(tbl=tbl, old_discharge=old_discharge, new_discharge=self.meas.discharge)

        # Heading Source
        elif column == 3:
            if self.h_external_valid:
                # Intialize dialog
                h_source_dialog = HSource(self)
                h_source_entered = h_source_dialog.exec_()
                # If data entered.
                with self.wait_cursor():
                    if h_source_entered:
                        old_discharge = self.meas.discharge
                        if h_source_dialog.rb_internal:
                            h_source = 'internal'
                        else:
                            h_source = 'external'

                        # Apply change to selected or all transects
                        if h_source_dialog.rb_all.isChecked():
                            self.meas.change_h_source(h_source=h_source)
                        else:
                            self.meas.change_h_source(h_source=h_source, transect_idx=self.transects_2_use[row])

                        # Update compass tab
                        self.update_compass_tab(tbl=tbl, old_discharge=old_discharge, new_discharge=self.meas.discharge)

    def select_calibration(self, row, column):
        """Displays selected compass calibration.

        Parameters
        ==========
        row: int
            row in table clicked by user
        column: int
            column in table clicked by user
        """
        if column == 0:
            with self.wait_cursor():
                # Set all files to normal font
                for nrow in range(self.table_compass_cal.rowCount()):
                    self.table_compass_cal.item(nrow, 0).setFont(self.font_normal)
                for nrow in range(self.table_compass_eval.rowCount()):
                    self.table_compass_eval.item(nrow, 0).setFont(self.font_normal)

                # Set selected file to bold font
                self.table_compass_cal.item(row, 0).setFont(self.font_bold)

                # Update contour and shiptrack plot
                self.compass_cal_eval(idx_cal=row)

    def select_evaluation(self, row, column):
        """Displays selected compass evaluation.

        Parameters
        ==========
        row: int
            row in table clicked by user
        column: int
            column in table clicked by user
        """

        if column == 0:
            with self.wait_cursor():
                # Set all files to normal font
                for nrow in range(self.table_compass_cal.rowCount()):
                    self.table_compass_cal.item(nrow, 0).setFont(self.font_normal)
                for nrow in range(self.table_compass_eval.rowCount()):
                    self.table_compass_eval.item(nrow, 0).setFont(self.font_normal)

                # Set selected file to bold font
                self.table_compass_eval.item(row, 0).setFont(self.font_bold)

                # Update contour and shiptrack plot
                self.compass_cal_eval(idx_eval=row)

    def compass_plot(self):
        """Generates the graph of heading and magnetic change.
        """

        # If figure already exists update it. If not, create it.
        if hasattr(self, 'heading_mpl'):
            self.heading_mpl.fig.clear()
            self.heading_mpl.heading_plot(qrev=self)

        else:
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_heading)

            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)

            # Create graph
            self.heading_mpl = Qtmpl(self.graphics_main_timeseries, width=6, height=2, dpi=80)
            self.heading_mpl.heading_plot(qrev=self)
            layout.addWidget(self.heading_mpl)

        # Draw canvas
        self.heading_mpl.draw()

    def pr_plot(self):
        """Generates the graph of heading and magnetic change.
        """

        # If figure already exists update it. If not, create it.
        if hasattr(self, 'pr_mpl'):
            self.pr_mpl.fig.clear()
            self.pr_mpl.pr_plot(qrev=self)

        else:
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_pr)

            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)

            # Create graph
            self.pr_mpl = Qtmpl(self.graphics_main_timeseries, width=4, height=2, dpi=80)
            self.pr_mpl.pr_plot(qrev=self)
            layout.addWidget(self.pr_mpl)

        # Draw canvas
        self.pr_mpl.draw()

# Temperature & Salinity Tab
# ==========================
    def tempsal_tab(self):
        """Initialize tempsal tab and associated settings.
        """

        # Setup data table
        tbl = self.table_tempsal
        table_header = [self.tr('Transect'),
                        self.tr('Temperature \n Source'),
                        self.tr('Average \n Temperature'),
                        self.tr('Average \n Salinity (ppt)'),
                        self.tr('Speed of \n Sound Source'),
                        self.tr('Speed of \n Sound' + self.units['label_V']),
                        self.tr('Discharge \n Previous \n' + self.units['label_Q']),
                        self.tr('Discharge \n Now \n' + self.units['label_Q']),
                        self.tr('Discharge \n % Change')]
        ncols = len(table_header)
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.cellClicked.connect(self.tempsal_table_clicked)

        # Connect temperature units radio buttons
        self.rb_c.toggled.connect(self.change_temp_units)
        self.rb_f.toggled.connect(self.change_temp_units)

        # Setup input validator for independent and adcp user temperature
        reg_ex = QRegExp("^[1-9]\d*(\.\d+)?$")
        input_validator = QtGui.QRegExpValidator(reg_ex, self)

        # Connect independent and adcp input option
        self.ed_user_temp.setValidator(input_validator)
        self.ed_adcp_temp.setValidator(input_validator)
        self.pb_ind_temp_apply.clicked.connect(self.apply_user_temp)
        self.pb_adcp_temp_apply.clicked.connect(self.apply_adcp_temp)
        self.ed_user_temp.textChanged.connect(self.user_temp_changed)
        self.ed_adcp_temp.textChanged.connect(self.adcp_temp_changed)

        # Update the table, independent, and user temperatures
        self.update_tempsal_tab(tbl=tbl, old_discharge=self.meas.discharge,
                                new_discharge=self.meas.discharge)

        # Display the times series plot of ADCP temperatures
        self.plot_temperature()

    def update_tempsal_tab(self, tbl, old_discharge, new_discharge):
        """Updates all data displayed on the tempsal tab.

        Parameters
        ==========
        tbl: QWidget
            Reference to QTableWidget
        old_discharge: float
            Discharge before any change
        new_discharge: float
            Discharge after change applied
        """

        # Initialize array to accumalate all temperature data
        temp_all = np.array([])

        for row in range(tbl.rowCount()):
            # Identify transect associated with the row
            transect_id = self.checked_transects_idx[row]

            # File/transect name
            col = 0
            checked = QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].file_name[:-4])
            checked.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(checked))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Temperature source
            col += 1
            item = 'Internal (ADCP)'
            if self.meas.transects[transect_id].sensors.speed_of_sound_mps.selected == 'user':
                item = 'User'
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Average temperature for transect
            col += 1
            temp = getattr(self.meas.transects[transect_id].sensors.temperature_deg_c,
                           self.meas.transects[transect_id].sensors.temperature_deg_c.selected)
            if self.rb_f.isChecked():
                temp = convert_temperature(temp_in=temp.data, units_in='C', units_out='F')
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(np.nanmean(temp.data))))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Salinity for transect
            col += 1
            sal = getattr(self.meas.transects[transect_id].sensors.salinity_ppt,
                           self.meas.transects[transect_id].sensors.salinity_ppt.selected)
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(np.nanmean(sal.data))))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Speed of sound source
            col += 1
            item = 'User'
            if self.meas.transects[transect_id].sensors.temperature_deg_c.selected == 'internal':
                if self.meas.transects[transect_id].sensors.temperature_deg_c.internal.source == 'Calculated':
                    item = 'Internal (ADCP)'
                else:
                    item = 'Computed'
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Average speed of sound
            col += 1
            sos = getattr(self.meas.transects[transect_id].sensors.speed_of_sound_mps,
                           self.meas.transects[transect_id].sensors.speed_of_sound_mps.selected)
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(np.nanmean(sos.data))))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Discharge before changes
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(old_discharge[transect_id].total)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Discharge after changes
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(new_discharge[transect_id].total)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Percent change in discharge
            col += 1
            per_change = ((new_discharge[transect_id].total - old_discharge[transect_id].total)
                          / old_discharge[transect_id].total) * 100
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(per_change)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Accumulate all temperature data in a single array used to compute mean temperature
            temp_all = np.append(temp_all, self.meas.transects[transect_id].sensors.temperature_deg_c.internal.data)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        # Display independent temperature reading if available
        if np.isnan(self.meas.ext_temp_chk['user']) == False:
            try:
                temp = float(self.meas.ext_temp_chk['user'])
                if self.rb_f.isChecked():
                    temp = convert_temperature(self.meas.ext_temp_chk['user'])
                self.ed_user_temp.setText('{:3.1f}'.format(temp))
                self.pb_ind_temp_apply.setEnabled(False)
            except (ValueError, TypeError) as e:
                user = None

        # Display user provided adcp temperature reading if available
        if np.isnan(self.meas.ext_temp_chk['adcp']) == False:
            try:
                temp = float(self.meas.ext_temp_chk['adcp'])
                if self.rb_f.isChecked():
                    temp = convert_temperature(self.meas.ext_temp_chk['adcp'])
                self.ed_adcp_temp.setText('{:3.1f}'.format(temp))
                self.pb_adcp_temp_apply.setEnabled(False)
            except (ValueError, TypeError) as e:
                user = None

        # Display mean temperature measured by ADCP
        temp = np.nanmean(temp_all)
        if self.rb_f.isChecked():
            temp = convert_temperature(temp, 'F', 'C')
        self.txt_adcp_avg.setText('{:3.1F}'.format(temp))

        # Display comments and messages in messages tab
        self.tempsal_comments_messages()

    def tempsal_table_clicked(self, row, column):
        """Coordinates changes to the temperature, salinity, and speed of sound settings based on the column in
        the table clicked by the user.

        Parameters
        ----------
        row: int
            row clicked by user
        column: int
            column clicked by user
        """

        tbl = self.table_tempsal

        # Change temperature
        if column == 1:
            user_temp = None

            # Intialize dialog for user input
            t_source_dialog = TempSource(self)
            t_source_entered = t_source_dialog.exec_()

            if t_source_entered:
                # Assign data based on change made by user
                old_discharge = self.meas.discharge
                if t_source_dialog.rb_internal:
                    t_source = 'internal'
                elif t_source_dialog.rb_user:
                    t_source = 'user'
                    user_temp = float(t_source_dialog.ed_user_temp.text())

                # Apply change to all or only selected transect based on user input
                if t_source_dialog.rb_all.isChecked():
                    self.meas.change_sos(parameter='temperatureSrc',
                                         temperature=user_temp,
                                         selected=t_source)
                else:
                    self.meas.change_sos(transect_idx=self.transects_2_use[row],
                                         parameter='temperatureSrc',
                                         temperature=user_temp,
                                         selected=t_source)

                # Update the tempsal tab
                self.update_tempsal_tab(tbl=tbl, old_discharge=old_discharge, new_discharge=self.meas.discharge)
                self.change = True

        # Change salinity
        elif column == 3:

            # Intialize dialog for user input
            salinity_dialog = Salinity(self)
            salinity_entered = salinity_dialog.exec_()

            if salinity_entered:
                # Assign data based on change made by user
                old_discharge = self.meas.discharge
                salinity = float(salinity_dialog.ed_magvar.text())

                # Apply change to all or only selected transect based on user input
                if salinity_dialog.rb_all.isChecked():
                    self.meas.change_sos(parameter='salinity',
                                         salinity=salinity)
                else:
                    self.meas.change_sos(transect_idx=self.transects_2_use[row],
                                         parameter='salinity',
                                         salinity=salinity)
                # Update the tempsal tab
                self.update_tempsal_tab(tbl=tbl, old_discharge=old_discharge, new_discharge=self.meas.discharge)
                self.change = True
        # Change speed of sound
        elif column == 5:
            user_sos = None

            # Intialize dialog for user input
            sos_source_dialog = SOSSource(self)
            sos_source_entered = sos_source_dialog.exec_()

            if sos_source_entered:
                # Assign data based on change made by user
                old_discharge = self.meas.discharge
                if sos_source_dialog.rb_internal:
                    sos_source = 'internal'
                elif sos_source_dialog.rb_user:
                    sos_source = 'user'
                    user_sos = float(sos_source_dialog.ed_user_temp.text())

                # Apply change to all or only selected transect based on user input
                if sos_source_dialog.rb_all.isChecked():
                    self.meas.change_sos(parameter='sosSrc',
                                         speed=user_sos,
                                         selected=sos_source)
                else:
                    self.meas.change_sos(transect_idx=self.transects_2_use[row],
                                         parameter='sosSrc',
                                         speed=user_sos,
                                         selected=sos_source)

                # Update the tempsal tab
                self.update_tempsal_tab(tbl=tbl, old_discharge=old_discharge, new_discharge=self.meas.discharge)
                self.change = True

    def tempsal_comments_messages(self):
        """Displays comments and messages associated with temperature, salinity, and speed of sound in Messages tab.
        """

        # Clear comments and messages
        self.display_tempsal_comments.clear()
        self.display_tempsal_messages.clear()

        if hasattr(self, 'meas'):
            # Display each comment on a new line
            self.display_tempsal_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_tempsal_comments.textCursor().insertText(comment)
                self.display_tempsal_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_tempsal_comments.textCursor().insertBlock()

            # Display each message on a new line
            self.display_tempsal_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.temperature['messages']:
                self.display_tempsal_messages.textCursor().insertText(message[0])
                self.display_tempsal_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_tempsal_messages.textCursor().insertBlock()

    def plot_temperature(self):
        """Generates the graph of temperature.
        """

        # If figure already exists update it. If not, create it.
        if hasattr(self, 'temperature_mpl'):
            self.temperature_mpl.fig.clear()
            self.temperature_mpl.temperature_plot(qrev=self)

        else:
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_temperature)

            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)

            # Create plot
            self.temperature_mpl = Qtmpl(self.graphics_main_timeseries, width=4, height=2, dpi=80)
            self.temperature_mpl.temperature_plot(qrev=self)
            layout.addWidget(self.temperature_mpl)

        # Draw canvas
        self.temperature_mpl.draw()

    def change_temp_units(self):
        """Updates the display when the user changes the temperature units. Note: changing the units does not
        change the actual data only the units used to display the data.
        """

        self.update_tempsal_tab(tbl=self.table_tempsal, old_discharge=self.meas.discharge,
                                new_discharge=self.meas.discharge, initial=0)

        self.plot_temperature()

    def apply_user_temp(self):
        """Applies a user entered value for the independent temperature. This change does not affect the measured
        discharge but could change the automatic QA/QC messages.
        """

        # Set cursor focus onto the table to avoid multiple calls the the adcp_temp_changed funtion
        self.table_tempsal.setFocus()

        # If data has been entered, convert the data to Celsius if necessary
        if len(self.ed_user_temp.text()) > 0:
            temp = float(self.ed_user_temp.text())
            if self.rb_f.isChecked():
                temp = convert_temperature(temp, 'F', 'C')
        else:
            temp = []

        # Update the measurement with the new ADCP temperature
        self.meas.ext_temp_chk['user'] = temp

        # Apply qa checks
        self.meas.qa.temperature_qa(self.meas)

        # Update GUI
        self.tempsal_comments_messages()
        self.pb_ind_temp_apply.setEnabled(False)
        self.change = True

    def apply_adcp_temp(self):
        """Applies a user entered value for the ADCP temperature. This change does not affect the measured
        discharge but could change the automatic QA/QC messages.
        """

        # Set cursor focus onto the table to avoid multiple calls the the adcp_temp_changed funtion
        self.table_tempsal.setFocus()

        # If data has been entered, convert the data to Celsius if necessary
        if len(self.ed_adcp_temp.text()) > 0:
            temp = float(self.ed_adcp_temp.text())
            if self.rb_f.isChecked():
                temp = convert_temperature(temp, 'F', 'C')
        else:
            temp = []

        # Update the measurement with the new ADCP temperature
        self.meas.ext_temp_chk['adcp'] = temp

        # Apply qa checks
        self.meas.qa.temperature_qa(self.meas)

        # Update GUI
        self.tempsal_comments_messages()
        self.pb_adcp_temp_apply.setEnabled(False)
        self.change = True

    def user_temp_changed(self):
        """Enables the apply button if the user enters a valid value in the independent temp box.
        """
        self.pb_ind_temp_apply.setEnabled(True)

    def adcp_temp_changed(self):
        """Enables the apply button if the user enters a valid value in the ADCP temp box.
        """
        self.pb_adcp_temp_apply.setEnabled(True)

# Moving-Bed Test Tab
# ===================
    def movbedtst_tab(self):
        """Initialize, setup settings, and display initial data in moving-bed test tab.
                """

        # Setup data table
        tbl = self.table_moving_bed
        table_header = [self.tr('User \n Valid'),
                        self.tr('Used for \n Correction'),
                        self.tr('Filename'),
                        self.tr('Type'),
                        self.tr('Duration \n (s)'),
                        self.tr('Distance \n Upstream' + self.units['label_L']),
                        self.tr('Moving-Bed \n Speed' + self.units['label_V']),
                        self.tr('Moving-Bed \n Direction (deg)'),
                        self.tr('Flow \n Speed' + self.units['label_V']),
                        self.tr('Flow \n Direction (deg)'),
                        self.tr('% Invalid \n BT'),
                        self.tr('Compass \n Error (deg'),
                        self.tr('% Moving \n Bed'),
                        self.tr('Moving \n Bed'),
                        self.tr('Quality')]
        ncols = len(table_header)
        nrows = len(self.meas.mb_tests)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.cellClicked.connect(self.mb_table_clicked)

        # Automatically resize rows and columns
        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        # Initialize checkbox settings
        self.cb_mb_bt.setCheckState(QtCore.Qt.Checked)
        self.cb_mb_gga.setCheckState(QtCore.Qt.Unchecked)
        self.cb_mb_vtg.setCheckState(QtCore.Qt.Unchecked)
        self.cb_mb_vectors.setCheckState(QtCore.Qt.Checked)

        # Connect plot variable checkboxes
        self.cb_mb_bt.stateChanged.connect(self.mb_plot_change)
        self.cb_mb_gga.stateChanged.connect(self.mb_plot_change)
        self.cb_mb_vtg.stateChanged.connect(self.mb_plot_change)
        self.cb_mb_vectors.stateChanged.connect(self.mb_plot_change)

        # Display content
        self.update_mb_table()
        self.mb_plots(idx=0)
        self.mb_comments_messages()

    def update_mb_table(self):
        """Populates the moving-bed table with the current settings and data.
        """
        with self.wait_cursor():

            tbl = self.table_moving_bed
            # Populate each row
            for row in range(tbl.rowCount()):

                # User Valid
                col = 0
                checked = QtWidgets.QTableWidgetItem('')
                checked.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(checked))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if self.meas.mb_tests[row].user_valid:
                    tbl.item(row, col).setCheckState(QtCore.Qt.Checked)
                else:
                    tbl.item(row, col).setCheckState(QtCore.Qt.Unchecked)

                # Use for Correction
                col += 1
                checked2 = QtWidgets.QTableWidgetItem('')
                checked2.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(checked2))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if self.meas.mb_tests[row].use_2_correct:
                    tbl.item(row, col).setCheckState(QtCore.Qt.Checked)
                else:
                    tbl.item(row, col).setCheckState(QtCore.Qt.Unchecked)

                # Filename
                col += 1
                item = os.path.basename(self.meas.mb_tests[row].transect.file_name)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item[:-4]))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                if self.meas.mb_tests[row].selected:
                    tbl.item(row, col).setFont(self.font_bold)

                # Type
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(self.meas.mb_tests[row].type))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Duration
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:4.1f}'.format(self.meas.mb_tests[row].duration_sec)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Distance Upstream
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:4.1f}'.format(self.meas.mb_tests[row].dist_us_m * self.units['L'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Moving-Bed Speed
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.2f}'.format(self.meas.mb_tests[row].mb_spd_mps * self.units['V'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Moving-Bed Direction
                col += 1
                if type(self.meas.mb_tests[row].mb_dir) is not list:
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(self.meas.mb_tests[row].mb_dir)))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Flow Speed
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(
                    self.meas.mb_tests[row].flow_spd_mps * self.units['V'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Flow Direction
                col += 1
                if type(self.meas.mb_tests[row].flow_dir) is not list:
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(self.meas.mb_tests[row].flow_dir)))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent Invalid BT
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(
                    self.meas.mb_tests[row].percent_invalid_bt)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Compass Error
                col += 1
                if type(self.meas.mb_tests[row].compass_diff_deg) is not list:
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(
                        self.meas.mb_tests[row].compass_diff_deg)))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent Moving Bed
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(
                    self.meas.mb_tests[row].percent_mb)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Moving Bed
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(self.meas.mb_tests[row].moving_bed))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Quality
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(self.meas.mb_tests[row].test_quality))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Automatically resize rows and columns
                tbl.resizeColumnsToContents()
                tbl.resizeRowsToContents()

    def mb_table_clicked(self, row, column):
        """Manages actions caused by the user clicking in selected columns of the table.

        Parameters
        ==========
        row: int
            row in table clicked by user
        column: int
            column in table clicked by user
        """

        tbl = self.table_moving_bed
        reprocess_measurement = True

        # User valid
        if column == 0:
            if  tbl.item(row, 0).checkState()== QtCore.Qt.Checked:
                tbl.item(row, 0).setCheckState(QtCore.Qt.Unchecked)
                self.meas.mb_tests[row].user_valid = False
            else:
                tbl.item(row, 0).setCheckState(QtCore.Qt.Checked)
                self.meas.mb_tests[row].user_valid = True

            self.meas.mb_tests = MovingBedTests.auto_use_2_correct(
                moving_bed_tests=self.meas.mb_tests,
                boat_ref=self.meas.transects[self.checked_transects_idx[0].w_vel.nav_ref])

        # Use to correct, manual override
        if column == 1:
            quality = tbl.item(row, 14).text()

            if quality == 'Manual':
                # Cancel Manual
                tbl.item(row, 1).setCheckState(QtCore.Qt.Unchecked)
                self.meas.mb_tests[row].use_2_correct == False
                self.meas.mb_tests[row].moving_bed == 'Unknown'
                self.meas.mb_tests[row].selected == False
                self.meas.mb_tests[row].test_quality = "Errors"
                self.meas.mb_tests = MovingBedTests.auto_use_2_correct(
                    moving_bed_tests=self.meas.mb_tests,
                    boat_ref=self.meas.transects[self.checked_transects_idx[0].w_vel.nav_ref])

            elif quality == 'Errors':
                # Manual override
                # Warn user and force acknowledgement before proceeding
                user_warning = QtWidgets.QMessageBox.question(self, 'Moving-Bed Test Manual Override',
                                                              'QRev has determined this moving-bed test has '
                                                              'critical errors and does not recommend using it '
                                                              'for correction. If you choose to use the test '
                                                              'anyway you will be required to justify its use.',
                                                              QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
                                                              QtWidgets.QMessageBox.Cancel)
                if user_warning == QtWidgets.QMessageBox.Ok:
                    # Apply manual override
                    self.addComment()
                    tbl.item(row, 1).setCheckState(QtCore.Qt.Checked)
                    self.meas.mb_tests[row].use_2_correct == True
                    self.meas.mb_tests[row].moving_bed == 'Yes'
                    self.meas.mb_tests[row].selected == True
                    self.meas.mb_tests[row].test_quality = "Manual"
                    self.meas.mb_tests = MovingBedTests.auto_use_2_correct(
                        moving_bed_tests=self.meas.mb_tests,
                        boat_ref=self.meas.transects[self.checked_transects_idx[0].w_vel.nav_ref])
                else:
                    tbl.item(row, 1).setCheckState(QtCore.Qt.Unchecked)
                    reprocess_measurement = False

            elif tbl.item(row, 13) == 'Yes':
                # Apply setting
                tbl.item(row, 1).setCheckState(QtCore.Qt.Checked)
                self.meas.mb_tests[row].use_2_correct == True

                # Check to make sure the selected test are of the same type
                test_type = []
                test_quality = []
                for test in self.meas.mb_tests:
                    if test.selected:
                        test_type = test.type
                        test_quality = test.quality
                unique_types = set(test_type)
                if len(unique_types) == 1:

                    # Check for errors
                    if 'Errors' not in test_quality:

                        # Multiple loops not allowed
                        if test_type == 'Loop' and len(test_type) > 1:
                            self.meas.mb_tests[row].use_2_correct == False
                            reprocess_measurement = False
                            tbl.item(row, 1).setCheckState(QtCore.Qt.Unchecked)
                            user_warning = QtWidgets.QMessageBox.question(self, 'Multiple Loop Test Warning',
                                                                          'Only one loop can be applied. '
                                                                          'Select the best loop.',
                                                                          QtWidgets.QMessageBox.Ok,
                                                                          QtWidgets.QMessageBox.Ok)


                else:
                    # Mixing of stationary and loop tests are not allowed
                    self.meas.mb_tests[row].use_2_correct == False
                    reprocess_measurement = False
                    user_warning = QtWidgets.QMessageBox.question(self, 'Mixed Moving-Bed Test Warning',
                                                                  'Application of mixed moving-bed test types is '
                                                                  'not allowed. Select only one loop or one or '
                                                                  'more stationary test.',
                                                                  QtWidgets.QMessageBox.Ok,
                                                                  QtWidgets.QMessageBox.Ok)


            else:
                # No moving-bed, so no moving-bed correction is applied
                tbl.item(row, 1).setCheckState(QtCore.Qt.Unchecked)
                reprocess_measurement = False

            # If changes were made reprocess the measurement
            if reprocess_measurement:
                self.meas.compute_discharge()
                self.uncertainty.compute_uncertainty(self)
                self.meas.qa.moving_bed_qa(self.meas)

        # Data to plot
        elif column == 2:
           self.mb_plots(idx=row)

    def mb_plots(self, idx=0):
        """Creates graphics specific to the type of moving-bed test.

        Parameters
        ----------
        idx: int
            Index of the test to be plotted.
        """

        if len(self.meas.mb_tests) > 0:
            # Show name of test plotted
            item = os.path.basename(self.meas.mb_tests[idx].transect.file_name)
            self.txt_mb_plotted.setText(item[:-4])

            # Always show the shiptrack plot
            self.mb_shiptrack(transect=self.meas.mb_tests[idx].transect)

            # Determine what plots to display based on test type
            if self.meas.mb_tests[idx].type == 'Loop':
                self.mb_boat_speed(transect=self.meas.mb_tests[idx].transect)
            else:
                self.stationary(mb_test=self.meas.mb_tests[idx])
        else:
            # Disable user checkboxes if no tests are available
            self.cb_mb_bt.setEnabled(False)
            self.cb_mb_gga.setEnabled(False)
            self.cb_mb_vtg.setEnabled(False)
            self.cb_mb_vectors.setEnabled(False)

    def mb_shiptrack(self, transect):
        """Creates shiptrack plot for data in transect.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData with data to be plotted.
        """

        # If the canvas has not been previously created, create the canvas and add the widget.
        if not hasattr(self, 'mb_shiptrack_canvas'):
            # Create the canvas
            self.mb_shiptrack_canvas = MplCanvas(parent=self.graph_mb_st, width=4, height=4, dpi=80)
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_mb_st)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.mb_shiptrack_canvas)

        # Initialize the shiptrack figure and assign to the canvas
        self.mb_shiptrack_fig = Shiptrack(canvas=self.mb_shiptrack_canvas)
        # Create the figure with the specified data
        self.mb_shiptrack_fig.create(transect=transect,
                                     units=self.units,
                                     cb=True,
                                     cb_bt=self.cb_mb_bt,
                                     cb_gga=self.cb_mb_gga,
                                     cb_vtg=self.cb_mb_vtg,
                                     cb_vectors=self.cb_mb_vectors)

        # Draw canvas
        self.mb_shiptrack_canvas.draw()

    def mb_boat_speed(self, transect):
        """Creates boat speed plot for data in transect.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData with data to be plotted.
        """

        # If the canvas has not been previously created, create the canvas and add the widget.
        if not hasattr(self, 'mb_ts_canvas'):
            # Create the canvas
            self.mb_ts_canvas = MplCanvas(parent=self.graph_mb_ts, width=8, height=2, dpi=80)
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_mb_ts)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.mb_ts_canvas)

        # Initialize the boat speed figure and assign to the canvas
        self.mb_ts_fig = BoatSpeed(canvas=self.mb_ts_canvas)
        # Create the figure with the specified data
        self.mb_ts_fig.create(transect=transect,
                                     units=self.units,
                                     cb=True,
                                     cb_bt=self.cb_mb_bt,
                                     cb_gga=self.cb_mb_gga,
                                     cb_vtg=self.cb_mb_vtg)

        # Draw canvas
        self.mb_ts_canvas.draw()

    def stationary(self, mb_test):
        """Creates the plots for analyzing stationary moving-bed tests.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData with data to be plotted.
        """

        # If the canvas has not been previously created, create the canvas and add the widget.
        if not hasattr(self, 'mb_ts_canvas'):
            # Create the canvas
            self.mb_ts_canvas = MplCanvas(parent=self.graph_mb_ts, width=8, height=2, dpi=80)
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_mb_ts)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add canvas
            layout.addWidget(self.mb_ts_canvas)

        # Initialize the stationary figure and assign to the canvas
        self.mb_ts_fig = StationaryGraphs(canvas=self.mb_ts_canvas)
        # Create the figure with the specified data
        self.mb_ts_fig.create(mb_test=mb_test, units=self.units)
        # Draw canvas
        self.mb_ts_canvas.draw()

    def mb_plot_change(self):
        """Coordinates changes in what references should be displayed in the boat speed and shiptrack plots.
        """

        # Shiptrack
        self.mb_shiptrack_fig.change()

        # Boat speed
        # Note if mb_ts_fig is set to stationary the StationaryGraphs class has a change method with does nothing,
        # to maintain compatibility.
        self.mb_ts_fig.change()

    def mb_comments_messages(self):
        """Displays comments and messages associated with moving-bed tests in Messages tab.
        """

        # Clear comments and messages
        self.display_mb_comments.clear()
        self.display_mb_messages.clear()

        if hasattr(self, 'meas'):
            # Display each comment on a new line
            self.display_mb_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_mb_comments.textCursor().insertText(comment)
                self.display_mb_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_mb_comments.textCursor().insertBlock()

            # Display each message on a new line
            self.display_mb_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.moving_bed['messages']:
                self.display_mb_messages.textCursor().insertText(message[0])
                self.display_mb_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_mb_messages.textCursor().insertBlock()

# Bottom track tab
# ================
#     def bt_tab(self):
#
#     def update_bt_table(self):
#
#     def change_bt_beam(self):
#
#     def change_bt_error(self):
#
#     def change_bt_vertical(self):
#
#     def change_bt_other(self):

# Split functions
# ==============
    def split_initialization(self, groupings=None, data=None):
        """Sets the GUI components to support semi-automatic processing of pairings that split a single
        measurement into multiple measurements. Loads the first pairing.

        Parameters
        ==========
        groupings: list
            This a list of lists of transect indices splitting a single measurement into multiple measurements
            Example groupings = [[0, 1], [2, 3, 4, 5], [8, 9]]
        data: Measurement
            Object of class Measurement which contains all of the transects to be grouped into multiple measurements
        """

        if groupings is not None:
            # GUI settings to allow processing to split measurement into multiple measurements
            self.save_all = False
            self.actionOpen.setEnabled(False)
            self.actionCheck.setEnabled(False)
            self.actionSave.setEnabled(True)
            self.actionComment.setEnabled(True)

            # Data settings
            self.meas = data
            self.groupings = groupings
            self.checked_transects_idx = Measurement.checked_transects(self.meas)
            self.h_external_valid = Measurement.h_external_valid(self.meas)

            # Process first pairing
            self.group_idx = 0
            self.checked_transects_idx = self.groupings[self.group_idx]
            self.split_processing(self.checked_transects_idx)

    def split_processing(self, group):
        """Creates the measurement based on the transect indices defined in group and updates the main tab with
        this new measurement data.

        Parameters
        ==========
        group: list
            List of transect indices that comprise a single measurement.
        """

        Measurement.selected_transects_changed(self.meas, selected_transects_idx=group)
        self.update_main()

    def split_save(self):
        """Saves the current measurement and automatically loads the next measurement based on the pairings. When
        the last pairing has been completed, returns control to the function initiating QRev.
        """

        # Create default file name
        save_file = SaveMeasurementDialog()

        # Save data in Matlab format
        if self.save_all:
            Python2Matlab.save_matlab_file(self.meas, save_file.full_Name)
        else:
            Python2Matlab.save_matlab_file(self.meas, save_file.full_Name, checked=self.groupings[self.group_idx])

        # Create a summary of the processed discharges
        discharge = Measurement.mean_discharges(self.meas)
        q = {'group': self.groupings[self.group_idx],
             'start_serial_time': self.meas.transects[self.groupings[self.group_idx][0]].date_time.start_serial_time,
             'end_serial_time': self.meas.transects[self.groupings[self.group_idx][-1]].date_time.end_serial_time,
             'processed_discharge': discharge['total_mean']}
        self.processed_data.append(q)

        # Load next pairing
        self.group_idx += 1

        # If all pairings have been processed return control to the function initiating QRev.
        if self.group_idx > len(self.groupings) - 1:
            self.caller.processed_meas = self.processed_data
            self.caller.Show_RIVRS()
            self.close()

        else:
            self.checked_transects_idx = self.groupings[self.group_idx]
            self.split_processing(self.checked_transects_idx)

# Support functions
# =================
    @contextmanager
    def wait_cursor(self):
        try:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            yield
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def tab_manager(self, tab_idx=None):
        """Manages the initialization of content for each tab and updates that information as necessary.

        Parameters
        ----------
        tab_idx: int
            Index of tab clicked by user
        """

        if tab_idx is None:
            tab_idx = self.current_tab
        else:
            self.current_tab = tab_idx

        if tab_idx == 0:
            # Show main tab
            if self.change:
                # If data has changed update main tab display
                self.update_main()
            else:
                self.tab_main.show()

        elif tab_idx == 1:
            # Show system tab
            self.system_tab()

        elif tab_idx == 2:
            # Show compass/pr tab
            self.compass_tab()

        elif tab_idx == 3:
            # Show temperature, salinity, speed of sound tab
            self.tempsal_tab()

        elif tab_idx == 4:
            # Moving-bed test tab
            self.movbedtst_tab()

# Command line functions
# ======================
    def set_command_arg(self, param_arg):
        self.command_arg = param_arg

    def handle_command_line_args(self):
        command = self.command_arg.split('=')[0].lower()
        if command == 'trdi' or command == 'trdichecked':
            file_name = arg.split('=')[1]
            self.meas = Measurement(in_file=file_name, source='TRDI', proc_type='QRev', checked=(command == 'trdichecked'))
            # self.update_meas(meas)
            self.update_main()

    def connect_and_emit_trigger(self):
        while not self.gui_initialized:
            time.sleep(0.2)
        self.handle_args_trigger.connect(window.handle_command_line_args)
        self.handle_args_trigger.emit()

# Main
# ====
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = QRev()
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        window.set_command_arg(arg)
        t = threading.Thread(target=window.connect_and_emit_trigger)
        t.start()
    window.show()
    app.exec_()
# elif __name__ == 'UI.MeasSplitter':
#     app = QtWidgets.QApplication(sys.argv)
#     window = QRev()
#     window.show()
#     app.exec_()