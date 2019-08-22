from PyQt5 import QtWidgets, QtCore, QtGui
# from Classes.stickysettings import StickySettings as SSet
from PyQt5.QtCore import pyqtSignal, QRegExp

import UI.QRev_gui as QRev_gui
import sys
import threading
import copy
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
from UI.BeamDepths import BeamDepths
from UI.Draft import Draft
from UI.CrossSection import CrossSection
from UI.StationaryGraphs import StationaryGraphs
from UI.BTFilters import BTFilters
from UI.GPSFilters import GPSFilters
from UI.WTContour import WTContour
from UI.WTFilters import WTFilters
from UI.Rating import Rating
from UI.ExtrapPlot import ExtrapPlot
from UI.Threshold import Threshold
from UI.Subsection import Subsection
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
        self.save_stylesheet = False
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
        self.tab_all.setEnabled(False)

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
            self.config_gui()
            self.processed_data = []
            self.processed_transects = []
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
                self.config_gui()
                self.change = True
                self.tab_manager(tab_idx=0)

    def save_measurement(self):
        """Save measurement in Matlab format.
        """
        # Create default file name
        save_file = SaveMeasurementDialog()

        if len(save_file.full_Name) > 0:
            # Save data in Matlab format
            if self.save_all:
                Python2Matlab.save_matlab_file(self.meas, save_file.full_Name)
            else:
                Python2Matlab.save_matlab_file(self.meas, save_file.full_Name, checked=self.checked_transects_idx)
            self.config_gui()

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
            self.update_comments()

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

        # Set dialog to current settings
        if self.units['ID'] == 'SI':
            self.options.rb_si.setChecked(True)
        else:
            self.options.rb_english.setChecked(True)

        if self.save_all:
            self.options.rb_All.setChecked(True)
        else:
            self.options.rb_checked.setChecked(True)

        if self.save_stylesheet:
            self.options.cb_stylesheet.setChecked(True)
        else:
            self.options.cb_stylesheet.setChecked(False)

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
            self.main_details_table()
            self.main_premeasurement_table()
            self.main_settings_table()
            self.main_adcp_table()
            self.messages_tab()
            self.comments_tab()
            if len(self.checked_transects_idx) > 0:
                self.contour_shiptrack(self.checked_transects_idx[0])
                self.main_extrap_plot()
                self.discharge_plot()
            else:
                if hasattr(self, 'extrap_mpl'):
                    self.extrap_mpl.fig.clear()
                    self.extrap_mpl.draw()
                if hasattr(self, 'middle_mpl'):
                    self.middle_mpl.fig.clear()
                    self.middle_mpl.draw()
                if hasattr(self, 'discharge_mpl'):
                    self.discharge_mpl.fig.clear()
                    self.discharge_mpl.draw()
            self.change = False
            print('complete')

    def update_toolbar_trans_select(self):
        """Updates the icon for the select transects on the toolbar.
        """
        self.actionCheck.setEnabled(True)
        self.tab_all.setEnabled(True)
        if len(self.checked_transects_idx) == len(self.meas.transects):
            self.actionCheck.setIcon(self.icon_allChecked)
        elif len(self.checked_transects_idx) > 0:
            self.actionCheck.setIcon(self.icon_unChecked)
        else:
            self.actionCheck.setIcon(self.icon_warning)
            self.tab_all.setEnabled(False)

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
        if len(self.checked_transects_idx) > 0:
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
        if len(self.checked_transects_idx) > 0:
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

    def main_extrap_plot(self):
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
        elif key == 'transects' or key == 'user':
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

        if len(self.checked_transects_idx) > 0:
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
        else:
            tbl.setRowCount(0)

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

        if len(self.checked_transects_idx) > 0:
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
                item = '{:10.2f}'.format(trans_prop['width'][transect_id] * self.units['L'])
                tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect area
                col += 1
                item = '{:10.2f}'.format(trans_prop['area'][transect_id] * self.units['A'])
                tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect average boat speed
                col += 1
                item = '{:6.2f}'.format(trans_prop['avg_boat_speed'][transect_id] * self.units['V'])
                tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect average boat course
                col += 1
                item = '{:6.2f}'.format(trans_prop['avg_boat_course'][transect_id])
                tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Transect average water speed
                col += 1
                item = '{:6.2f}'.format(trans_prop['avg_water_speed'][transect_id] * self.units['V'])
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
            item = '{:10.2f}'.format(trans_prop['width'][n_transects] * self.units['L'])
            tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Average area
            col += 1
            item = '{:10.2f}'.format(trans_prop['area'][n_transects] * self.units['A'])
            tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Average boat speed
            col += 1
            item = '{:6.2f}'.format(trans_prop['avg_boat_speed'][n_transects] * self.units['V'])
            tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Skip average boat course
            col += 1

            # Average water speed
            col += 1
            item = '{:6.2f}'.format(trans_prop['avg_water_speed'][n_transects] * self.units['V'])
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

        if len(self.checked_transects_idx) > 0:

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

        if len(self.checked_transects_idx) > 0:
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

        if len(self.checked_transects_idx) > 0:

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

                self.systest_comments_messages()

    def systest_comments_messages(self):

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
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(old_discharge[transect_id].total * self.units['Q'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge from new/current settings
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(new_discharge[transect_id].total * self.units['Q'])))
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
                    old_discharge = copy.deepcopy(self.meas.discharge)
                    magvar = float(magvar_dialog.ed_magvar.text())

                    # Apply change to selected or all transects
                    if magvar_dialog.rb_all.isChecked():
                        self.meas.change_magvar(magvar=magvar)
                    else:
                        self.meas.change_magvar( magvar=magvar, transect_idx=self.transects_2_use[row])

                    # Update compass tab
                    self.update_compass_tab(tbl=tbl, old_discharge=old_discharge, new_discharge=self.meas.discharge)
                    self.change = True

        # Heading Offset
        elif column == 2:
            if self.h_external_valid:
                # Intialize dialog
                h_offset_dialog = HOffset(self)
                h_offset_entered = h_offset_dialog.exec_()
                # If data entered.
                with self.wait_cursor():
                    if h_offset_entered:
                        old_discharge = copy.deepcopy(self.meas.discharge)
                        h_offset = float(h_offset_dialog.ed_hoffset.text())

                        # Apply change to selected or all transects
                        if h_offset_dialog.rb_all.isChecked():
                            self.meas.change_h_offset(h_offset=h_offset)
                        else:
                            self.meas.change_h_offset(h_offset=h_offset, transect_idx=self.transects_2_use[row])

                        # Update compass tab
                        self.update_compass_tab(tbl=tbl, old_discharge=old_discharge, new_discharge=self.meas.discharge)
                        self.change = True

        # Heading Source
        elif column == 3:
            if self.h_external_valid:
                # Intialize dialog
                h_source_dialog = HSource(self)
                h_source_entered = h_source_dialog.exec_()
                # If data entered.
                with self.wait_cursor():
                    if h_source_entered:
                        old_discharge = copy.deepcopy(self.meas.discharge)
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
                        self.change = True

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
            item = QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].file_name[:-4])
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
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
            temp_converted = temp.data
            if self.rb_f.isChecked():
                temp_converted = convert_temperature(temp_in=temp.data, units_in='C', units_out='F')
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(np.nanmean(temp_converted))))
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
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(old_discharge[transect_id].total * self.units['Q'])))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Discharge after changes
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(new_discharge[transect_id].total * self.units['Q'])))
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

        if np.isnan(self.meas.ext_temp_chk['user']):
            self.ed_user_temp.setText('')
            self.pb_ind_temp_apply.setEnabled(False)
        else:
            try:
                temp = float(self.meas.ext_temp_chk['user'])
                if self.rb_f.isChecked():
                    temp = convert_temperature(self.meas.ext_temp_chk['user'], units_in='C', units_out='F')
                self.ed_user_temp.setText('{:3.1f}'.format(temp))
                self.pb_ind_temp_apply.setEnabled(False)
            except (ValueError, TypeError) as e:
                user = None
                self.ed_user_temp.setText('')
                self.pb_ind_temp_apply.setEnabled(False)

        # Display user provided adcp temperature reading if available
        if np.isnan(self.meas.ext_temp_chk['adcp']) == False:
            try:
                temp = float(self.meas.ext_temp_chk['adcp'])
                if self.rb_f.isChecked():
                    temp = convert_temperature(self.meas.ext_temp_chk['adcp'], units_in='C', units_out='F')
                self.ed_adcp_temp.setText('{:3.1f}'.format(temp))
                self.pb_adcp_temp_apply.setEnabled(False)
            except (ValueError, TypeError) as e:
                user = None

        # Display mean temperature measured by ADCP
        temp = np.nanmean(temp_all)
        if self.rb_f.isChecked():
            temp = convert_temperature(temp, units_in='C', units_out='F')
        self.txt_adcp_avg.setText('{:3.1f}'.format(temp))

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
                old_discharge = copy.deepcopy(self.meas.discharge)
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
                old_discharge = copy.deepcopy(self.meas.discharge)
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
                old_discharge = copy.deepcopy(self.meas.discharge)
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
                                new_discharge=self.meas.discharge)

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
                item = '{:4.1f}'.format(self.meas.mb_tests[row].duration_sec)
                if 'nan' in item:
                    item = ''
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Distance Upstream
                col += 1
                item = '{:4.1f}'.format(self.meas.mb_tests[row].dist_us_m * self.units['L'])
                if 'nan' in item:
                    item = ''
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Moving-Bed Speed
                col += 1
                item = '{:3.2f}'.format(self.meas.mb_tests[row].mb_spd_mps * self.units['V'])
                if 'nan' in item:
                    item = ''
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Moving-Bed Direction
                col += 1

                if type(self.meas.mb_tests[row].mb_dir) is not list:
                    item = '{:3.1f}'.format(self.meas.mb_tests[row].mb_dir)
                    if 'nan' in item:
                        item = ''
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Flow Speed
                col += 1
                item = '{:3.1f}'.format(self.meas.mb_tests[row].flow_spd_mps * self.units['V'])
                if 'nan' in item:
                    item = ''
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Flow Direction
                col += 1
                if type(self.meas.mb_tests[row].flow_dir) is not list:
                    item = '{:3.1f}'.format(self.meas.mb_tests[row].flow_dir)
                    if 'nan' in item:
                        item = ''
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent Invalid BT
                col += 1
                item = '{:3.1f}'.format(self.meas.mb_tests[row].percent_invalid_bt)
                if 'nan' in item:
                    item = ''
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Compass Error
                col += 1
                if type(self.meas.mb_tests[row].compass_diff_deg) is not list:
                    item = '{:3.1f}'.format(self.meas.mb_tests[row].compass_diff_deg)
                    if 'nan' in item:
                        item = ''
                    tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                    tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent Moving Bed
                col += 1
                item = '{:3.1f}'.format(self.meas.mb_tests[row].percent_mb)
                if 'nan' in item:
                    item = ''
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Moving Bed
                col += 1
                item = self.meas.mb_tests[row].moving_bed
                if 'nan' in item:
                    item = ''
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Quality
                col += 1
                item = self.meas.mb_tests[row].test_quality
                if 'nan' in item:
                    item = ''
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
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
            if tbl.item(row, 0).checkState()== QtCore.Qt.Checked:
                # tbl.item(row, 0).setCheckState(QtCore.Qt.Unchecked)
                self.meas.mb_tests[row].user_valid = False
                self.addComment()
            else:
                # tbl.item(row, 0).setCheckState(QtCore.Qt.Checked)
                self.meas.mb_tests[row].user_valid = True

            self.meas.mb_tests = MovingBedTests.auto_use_2_correct(
                moving_bed_tests=self.meas.mb_tests,
                boat_ref=self.meas.transects[self.checked_transects_idx[0]].w_vel.nav_ref)
            self.meas.qa.moving_bed_qa(self.meas)
            self.change = True

        # Use to correct, manual override
        if column == 1:
            quality = tbl.item(row, 14).text()

            if quality == 'Manual':
                # Cancel Manual
                # tbl.item(row, 1).setCheckState(QtCore.Qt.Unchecked)
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
                    # tbl.item(row, 1).setCheckState(QtCore.Qt.Checked)
                    self.meas.mb_tests[row].use_2_correct == True
                    self.meas.mb_tests[row].moving_bed == 'Yes'
                    self.meas.mb_tests[row].selected == True
                    self.meas.mb_tests[row].test_quality = "Manual"
                    self.meas.mb_tests = MovingBedTests.auto_use_2_correct(
                        moving_bed_tests=self.meas.mb_tests,
                        boat_ref=self.meas.transects[self.checked_transects_idx[0].w_vel.nav_ref])
                else:
                    # tbl.item(row, 1).setCheckState(QtCore.Qt.Unchecked)
                    reprocess_measurement = False

            elif tbl.item(row, 13).text() == 'Yes':
                if tbl.item(row, 1).checkState() == QtCore.Qt.Checked:
                    # tbl.item(row, 1).setCheckState(QtCore.Qt.Unchecked)
                    self.meas.mb_tests[row].use_2_correct = False
                    self.addComment()
                else:
                    # Apply setting
                    # tbl.item(row, 1).setCheckState(QtCore.Qt.Checked)
                    self.meas.mb_tests[row].use_2_correct = True

                    # Check to make sure the selected test are of the same type
                    test_type = []
                    test_quality = []
                    for test in self.meas.mb_tests:
                        if test.selected:
                            test_type.append(test.type)
                            test_quality = test.test_quality
                    unique_types = set(test_type)
                    if len(unique_types) == 1:

                        # Check for errors
                        if 'Errors' not in test_quality:

                            # Multiple loops not allowed
                            if test_type == 'Loop' and len(test_type) > 1:
                                self.meas.mb_tests[row].use_2_correct == False
                                reprocess_measurement = False
                                # tbl.item(row, 1).setCheckState(QtCore.Qt.Unchecked)
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
                # tbl.item(row, 1).setCheckState(QtCore.Qt.Unchecked)
                reprocess_measurement = False
                user_warning = QtWidgets.QMessageBox.question(self, 'No Moving-Bed',
                                                              'There is no moving-bed. Correction cannot be applied. ',
                                                              QtWidgets.QMessageBox.Ok,
                                                              QtWidgets.QMessageBox.Ok)

            # If changes were made reprocess the measurement
            if reprocess_measurement:
                self.meas.compute_discharge()
                self.meas.uncertainty.compute_uncertainty(self.meas)
                self.meas.qa.moving_bed_qa(self.meas)
            self.change = True

        # Data to plot
        elif column == 2:
           self.mb_plots(idx=row)

        self.update_mb_table()
        # self.mb_plots(idx=0)
        self.mb_comments_messages()

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
    def bt_tab(self):
        """Initialize, setup settings, and display initial data in bottom track tab.
        """

        # Setup data table
        tbl = self.table_bt
        table_header = [self.tr('Filename'),
                        self.tr('Number or \n Ensembles'),
                        self.tr('Beam \n % <4'),
                        self.tr('Total \n % Invalid'),
                        self.tr('Orig Data \n % Invalid'),
                        self.tr('<4 Beam \n % Invalid'),
                        self.tr('Error Vel \n % Invalid'),
                        self.tr('Vert Vel \n % Invalid'),
                        self.tr('Other \n % Invalid'),
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
        tbl.cellClicked.connect(self.bt_table_clicked)

        # Automatically resize rows and columns
        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        # Initialize checkbox settings for boat reference
        self.cb_bt_bt.setCheckState(QtCore.Qt.Checked)
        self.cb_bt_gga.setCheckState(QtCore.Qt.Unchecked)
        self.cb_bt_vtg.setCheckState(QtCore.Qt.Unchecked)
        selected = self.meas.transects[self.checked_transects_idx[0]].boat_vel.selected
        if selected == 'gga_vel':
            self.cb_bt_gga.setCheckState(QtCore.Qt.Checked)
        elif selected == 'vtg_vel':
            self.cb_bt_vtg.setCheckState(QtCore.Qt.Checked)

        self.cb_bt_vectors.setCheckState(QtCore.Qt.Checked)

        # Connect plot variable checkboxes
        self.cb_bt_bt.stateChanged.connect(self.bt_plot_change)
        self.cb_bt_gga.stateChanged.connect(self.bt_plot_change)
        self.cb_bt_vtg.stateChanged.connect(self.bt_plot_change)
        self.cb_bt_vectors.stateChanged.connect(self.bt_plot_change)

        # Connect radio buttons
        self.rb_bt_beam.toggled.connect(self.bt_radiobutton_control)
        self.rb_bt_error.toggled.connect(self.bt_radiobutton_control)
        self.rb_bt_vert.toggled.connect(self.bt_radiobutton_control)
        self.rb_bt_other.toggled.connect(self.bt_radiobutton_control)

        # Connect manual entry
        self.ed_bt_error_vel_threshold.editingFinished.connect(self.change_error_vel_threshold)
        self.ed_bt_vert_vel_threshold.editingFinished.connect(self.change_vert_vel_threshold)

        # Connect filters
        self.combo_bt_3beam.currentIndexChanged[str].connect(self.change_bt_beam)
        self.combo_bt_error_velocity.activated[str].connect(self.change_bt_error)
        self.combo_bt_vert_velocity.currentIndexChanged[str].connect(self.change_bt_vertical)
        self.combo_bt_other.currentIndexChanged[str].connect(self.change_bt_other)

        # Transect selected for display
        self.transect = self.meas.transects[self.checked_transects_idx[0]]

        # Set beam filter from transect data
        if self.transect.boat_vel.bt_vel.beam_filter < 0:
            self.combo_bt_3beam.setCurrentIndex(0)
        elif self.transect.boat_vel.bt_vel.beam_filter == 3:
            self.combo_bt_3beam.setCurrentIndex(1)
        elif self.transect.boat_vel.bt_vel.beam_filter == 4:
            self.combo_bt_3beam.setCurrentIndex(2)
        else:
            self.combo_bt_3beam.setCurrentIndex(0)

        # Set error velocity filter from transect data
        index = self.combo_bt_error_velocity.findText(self.transect.boat_vel.bt_vel.d_filter, QtCore.Qt.MatchFixedString)
        self.combo_bt_error_velocity.setCurrentIndex(index)

        # Set vertical velocity filter from transect data
        index = self.combo_bt_vert_velocity.findText(self.transect.boat_vel.bt_vel.w_filter, QtCore.Qt.MatchFixedString)
        self.combo_bt_vert_velocity.setCurrentIndex(index)

        # Set smooth filter from transect data
        if self.transect.boat_vel.bt_vel.smooth_filter == 'Off':
            self.combo_bt_other.setCurrentIndex(0)
        elif self.transect.boat_vel.bt_vel.smooth_filter == 'On':
            self.combo_bt_other.setCurrentIndex(1)

        # Display content
        self.idx = 0
        self.update_bt_table(old_discharge=self.meas.discharge, new_discharge=self.meas.discharge)
        self.bt_plots()
        self.bt_comments_messages()

    def update_bt_table(self, old_discharge, new_discharge):
        """Updates the bottom track table with new or reprocessed data.

        Parameters
        ----------
        old_discharge: list
            List of objects of QComp with previous settings
        new_discharge: list
            List of objects of QComp with new settings
        """

        with self.wait_cursor():
            # Set tbl variable
            tbl = self.table_bt

            # Populate each row
            for row in range(tbl.rowCount()):
                # Identify transect associated with the row
                transect_id = self.checked_transects_idx[row]
                transect = self.meas.transects[transect_id]
                valid_data = transect.boat_vel.bt_vel.valid_data
                num_ensembles = len(valid_data[0,:])
                not_4beam = np.nansum(np.isnan(transect.boat_vel.bt_vel.d_mps))
                num_invalid = np.nansum(np.logical_not(valid_data[0, :]))
                num_orig_invalid = np.nansum(np.logical_not(valid_data[1, :]))
                num_beam_invalid = np.nansum(np.logical_not(valid_data[5, :]))
                num_error_invalid = np.nansum(np.logical_not(valid_data[2, :]))
                num_vert_invalid = np.nansum(np.logical_not(valid_data[3, :]))
                num_other_invalid = np.nansum(np.logical_not(valid_data[4, :]))

                # File/transect name
                col = 0
                item = QtWidgets.QTableWidgetItem(transect.file_name[:-4])
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                tbl.item(row, 0).setFont(self.font_normal)

                # Total number of ensembles
                col += 1
                item = '{:5d}'.format(num_ensembles)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Less than 4 beams
                col += 1
                item = '{:3.2f}'.format((not_4beam / num_ensembles) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Invalid total
                col += 1
                item = '{:3.2f}'.format((num_invalid / num_ensembles) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Invalid original data
                col += 1
                item = '{:3.2f}'.format((num_orig_invalid / num_ensembles) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Invalid 3 beam
                col += 1
                item = '{:3.2f}'.format((num_beam_invalid / num_ensembles) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Error velocity invalid
                col += 1
                item = '{:3.2f}'.format((num_error_invalid / num_ensembles) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Vertical velocity invalid
                col += 1
                item = '{:3.2f}'.format((num_vert_invalid / num_ensembles) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Other
                col += 1
                item = '{:3.2f}'.format((num_other_invalid / num_ensembles) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge before changes
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(old_discharge[transect_id].total * self.units['Q'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge after changes
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(new_discharge[transect_id].total * self.units['Q'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent change in discharge
                col += 1
                per_change = ((new_discharge[transect_id].total - old_discharge[transect_id].total)
                              / old_discharge[transect_id].total) * 100
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(per_change)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Set selected file to bold font
            tbl.item(self.idx, 0).setFont(self.font_bold)

            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

            self.bt_comments_messages()

    def bt_plots(self):
        """Creates graphics for BT tab.
        """

        with self.wait_cursor():
            # Set all filenames to normal font
            nrows = len(self.checked_transects_idx)
            for nrow in range(nrows):
                self.table_bt.item(nrow, 0).setFont(self.font_normal)

            # Set selected file to bold font
            self.table_bt.item(self.idx, 0).setFont(self.font_bold)

            # Determine transect selected
            transect_id = self.checked_transects_idx[self.idx]
            self.transect = self.meas.transects[transect_id]
            self.invalid_bt = np.logical_not(self.transect.boat_vel.bt_vel.valid_data)

            # Update plots
            self.bt_shiptrack()
            self.bt_boat_speed()
            self.bt_filter_plots()

    def bt_shiptrack(self):
        """Creates shiptrack plot for data in transect.
        """

        # If the canvas has not been previously created, create the canvas and add the widget.
        if not hasattr(self, 'bt_shiptrack_canvas'):
            # Create the canvas
            self.bt_shiptrack_canvas = MplCanvas(parent=self.graph_bt_st, width=4, height=4, dpi=80)
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_bt_st)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.bt_shiptrack_canvas)

        # Initialize the shiptrack figure and assign to the canvas
        self.bt_shiptrack_fig = Shiptrack(canvas=self.bt_shiptrack_canvas)
        # Create the figure with the specified data
        self.bt_shiptrack_fig.create(transect=self.transect,
                                     units=self.units,
                                     cb=True,
                                     cb_bt=self.cb_bt_bt,
                                     cb_gga=self.cb_bt_gga,
                                     cb_vtg=self.cb_bt_vtg,
                                     cb_vectors=self.cb_bt_vectors,
                                     invalid_bt=self.invalid_bt)

        # Draw canvas
        self.bt_shiptrack_canvas.draw()

    def bt_boat_speed(self):
        """Creates boat speed plot for data in transect.
        """

        # If the canvas has not been previously created, create the canvas and add the widget.
        if not hasattr(self, 'bt_bottom_canvas'):
            # Create the canvas
            self.bt_bottom_canvas = MplCanvas(parent=self.graph_bt_bottom, width=8, height=2, dpi=80)
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_bt_bottom)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.bt_bottom_canvas)

        # Initialize the boat speed figure and assign to the canvas
        self.bt_bottom_fig = BoatSpeed(canvas=self.bt_bottom_canvas)
        # Create the figure with the specified data
        self.bt_bottom_fig.create(transect=self.transect,
                                  units=self.units,
                                  cb=True,
                                  cb_bt=self.cb_bt_bt,
                                  cb_gga=self.cb_bt_gga,
                                  cb_vtg=self.cb_bt_vtg,
                                  invalid_bt=self.invalid_bt)

        # Draw canvas
        self.bt_bottom_canvas.draw()

    @QtCore.pyqtSlot()
    def bt_radiobutton_control(self):

        with self.wait_cursor():
            if self.sender().isChecked():
                self.bt_filter_plots()

    def bt_filter_plots(self):
        """Creates plots of filter characteristics.
        """

        # If the canvas has not been previously created, create the canvas and add the widget.
        if not hasattr(self, 'bt_top_canvas'):
            # Create the canvas
            self.bt_top_canvas = MplCanvas(parent=self.graph_bt_top, width=8, height=2, dpi=80)
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_bt_top)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.bt_top_canvas)

        # Initialize the boat speed figure and assign to the canvas
        self.bt_top_fig = BTFilters(canvas=self.bt_top_canvas)

        # Create the figure with the specified data
        if self.rb_bt_beam.isChecked():
            self.bt_top_fig.create(transect=self.transect,
                                   units=self.units, selected='beam')
        elif self.rb_bt_error.isChecked():
            self.bt_top_fig.create(transect=self.transect,
                                   units=self.units, selected='error')
        elif self.rb_bt_vert.isChecked():
            self.bt_top_fig.create(transect=self.transect,
                                   units=self.units, selected='vert')
        elif self.rb_bt_other.isChecked():
            self.bt_top_fig.create(transect=self.transect,
                                   units=self.units, selected='other')

        # Draw canvas
        self.bt_top_canvas.draw()

    def bt_table_clicked(self, row, column):
        """Changes plotted data to the transect of the transect clicked.

        Parameters
        ----------
        row: int
            Row clicked by user
        column: int
            Column clicked by user
        """

        if column == 0:
            self.idx = row
            self.bt_plots()

    @QtCore.pyqtSlot()
    def bt_plot_change(self):
        """Coordinates changes in what references should be displayed in the boat speed and shiptrack plots.
        """

        with self.wait_cursor():
            # Shiptrack
            self.bt_shiptrack_fig.change()
            self.bt_shiptrack_canvas.draw()

            # Boat speed
            self.bt_bottom_fig.change()
            self.bt_bottom_canvas.draw()

    def update_bt_tab(self, s):
        """Updates the measurement and bottom track tab (table and graphics) after a change to settings has been made.

        Parameters
        ----------
        s: dict
            Dictionary of all process settings for the measurement
        """

        # Save discharge from previous settings
        old_discharge = copy.deepcopy(self.meas.discharge)

        # Apply new settings
        self.meas.apply_settings(settings=s)

        # Update table
        self.update_bt_table(old_discharge=old_discharge, new_discharge=self.meas.discharge)

        # Update plots
        self.bt_plots()

    @QtCore.pyqtSlot(str)
    def change_bt_beam(self, text):
        """Coordinates user initiated change to the beam settings.

        Parameters
        ----------
        text: str
            User selection from combo box
        """

        with self.wait_cursor():

            # Get current settings
            s = self.meas.current_settings()

            if text == 'Auto':
                s['BTbeamFilter'] = -1
            elif text == 'Allow':
                s['BTbeamFilter'] = 3
            elif text == '4-Beam Only':
                s['BTbeamFilter'] = 4

            # Update measurement and display
            self.update_bt_tab(s)
            self.change = True

    @QtCore.pyqtSlot(str)
    def change_bt_error(self, text):
        """Coordinates user initiated change to the error velocity settings.

         Parameters
         ----------
         text: str
             User selection from combo box
         """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            s['BTdFilter'] = text
            if text == 'Manual':
                # If Manual enable the line edit box for user input. Updates are not applied until the user has entered
                # a value in the line edit box.
                self.ed_bt_error_vel_threshold.setEnabled(True)
            else:
                # If manual is not selected the line edit box is cleared and disabled and the updates applied.
                self.ed_bt_error_vel_threshold.setEnabled(False)
                self.ed_bt_error_vel_threshold.setText('')
                self.update_bt_tab(s)
            self.change = True


    @QtCore.pyqtSlot(str)
    def change_bt_vertical(self, text):
        """Coordinates user initiated change to the vertical velocity settings.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            s['BTwFilter'] = text

            if text == 'Manual':
                # If Manual enable the line edit box for user input. Updates are not applied until the user has entered
                # a value in the line edit box.
                self.ed_bt_vert_vel_threshold.setEnabled(True)
            else:
                # If manual is not selected the line edit box is cleared and disabled and the updates applied.
                self.ed_bt_vert_vel_threshold.setEnabled(False)
                self.ed_bt_vert_vel_threshold.setText('')
                self.update_bt_tab(s)
                self.change = True

    @QtCore.pyqtSlot(str)
    def change_bt_other(self, text):
        """Coordinates user initiated change to the vertical velocity settings.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            if text == 'Off':
                s['BTsmoothFilter'] = 'Off'
            elif text == 'Smooth':
                s['BTsmoothFilter'] = 'On'

            # Update measurement and display
            self.update_bt_tab(s)
            self.change = True

    @QtCore.pyqtSlot()
    def change_error_vel_threshold(self):
        """Coordinates application of a user specified error velocity threshold.
        """

        with self.wait_cursor():
            # Get threshold and convert to SI units
            threshold = float(self.ed_bt_error_vel_threshold.text()) / self.units['V']

            # Get current settings
            s = self.meas.current_settings()
            # Because editingFinished is used if return is pressed and later focus is changed the method could get
            # twice. This line checks to see if there was and actual change.
            if np.abs(threshold - s['BTdFilterThreshold']) > 0.0001:
                # Change settings to manual and the associated threshold
                s['BTdFilter'] = 'Manual'
                s['BTdFilterThreshold'] = threshold

                # Update measurement and display
                self.update_bt_tab(s)
                self.change = True

    @QtCore.pyqtSlot()
    def change_vert_vel_threshold(self):
        """Coordinates application of a user specified vertical velocity threshold.
        """

        with self.wait_cursor():
            # Get threshold and convert to SI units
            threshold = float(self.ed_bt_vert_vel_threshold.text()) / self.units['V']

            # Get current settings
            s = self.meas.current_settings()
            # Because editingFinished is used if return is pressed and later focus is changed the method could get
            # twice. This line checks to see if there was and actual change.
            if np.abs(threshold - s['BTwFilterThreshold']) > 0.0001:
                # Change settings to manual and the associated threshold
                s['BTwFilter'] = 'Manual'
                s['BTwFilterThreshold'] = threshold

                # Update measurement and display
                self.update_bt_tab(s)
                self.change = True

    def bt_comments_messages(self):
        """Displays comments and messages associated with bottom track filters in Messages tab.
        """

        # Clear comments and messages
        self.display_bt_comments.clear()
        self.display_bt_messages.clear()

        if hasattr(self, 'meas'):
            # Display each comment on a new line
            self.display_bt_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_bt_comments.textCursor().insertText(comment)
                self.display_bt_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_bt_comments.textCursor().insertBlock()

            # Display each message on a new line
            self.display_bt_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.bt_vel['messages']:
                self.display_bt_messages.textCursor().insertText(message[0])
                self.display_bt_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_bt_messages.textCursor().insertBlock()

# GPS tab
# =======
    def gps_tab(self):
        """Initialize, setup settings, and display initial data in gps tab.
        """

        # Setup data table
        tbl = self.table_gps
        table_header = [self.tr('Filename'),
                        self.tr('Number or \n Ensembles'),
                        self.tr('GGA \n % Invalid'),
                        self.tr('VTG \n % Invalid'),
                        self.tr('Diff. Qual. \n % Invalid'),
                        self.tr('Alt. Change \n % Invalid'),
                        self.tr('HDOP \n % Invalid'),
                        self.tr('Sat Change \n % '),
                        self.tr('Other \n % Invalid'),
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
        tbl.cellClicked.connect(self.gps_table_clicked)

        # Automatically resize rows and columns
        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        # Initialize checkbox settings for boat reference
        self.cb_gps_bt.setCheckState(QtCore.Qt.Checked)
        if self.meas.transects[self.checked_transects_idx[0]].boat_vel.gga_vel is not None:
            self.cb_gps_gga.setCheckState(QtCore.Qt.Checked)
        if self.meas.transects[self.checked_transects_idx[0]].boat_vel.vtg_vel is not None:
            self.cb_gps_vtg.setCheckState(QtCore.Qt.Checked)

        self.cb_gps_vectors.setCheckState(QtCore.Qt.Checked)

        # Connect plot variable checkboxes
        self.cb_gps_bt.stateChanged.connect(self.gps_plot_change)
        self.cb_gps_gga.stateChanged.connect(self.gps_plot_change)
        self.cb_gps_vtg.stateChanged.connect(self.gps_plot_change)
        self.cb_gps_vectors.stateChanged.connect(self.gps_plot_change)

        # Connect radio buttons
        self.rb_gps_quality.toggled.connect(self.gps_radiobutton_control)
        self.rb_gps_altitude.toggled.connect(self.gps_radiobutton_control)
        self.rb_gps_hdop.toggled.connect(self.gps_radiobutton_control)
        self.rb_gps_sats.toggled.connect(self.gps_radiobutton_control)
        self.rb_gps_other.toggled.connect(self.gps_radiobutton_control)

        # Connect manual entry
        self.ed_gps_altitude_threshold.editingFinished.connect(self.change_altitude_threshold)
        self.ed_gps_hdop_threshold.editingFinished.connect(self.change_hdop_threshold)

        # Connect filters
        self.combo_gps_qual.currentIndexChanged[str].connect(self.change_quality)
        self.combo_gps_altitude.currentIndexChanged[str].connect(self.change_altitude)
        self.combo_gps_hdop.currentIndexChanged[str].connect(self.change_hdop)
        self.combo_gps_other.currentIndexChanged[str].connect(self.change_gps_other)

        # Transect selected for display
        self.transect = self.meas.transects[self.checked_transects_idx[0]]

        # Set gps quality filter
        if self.transect.boat_vel.gga_vel.gps_diff_qual_filter == 1:
            self.combo_gps_qual.setCurrentIndex(0)
        elif self.transect.boat_vel.gga_vel.gps_diff_qual_filter == 2:
            self.combo_gps_qual.setCurrentIndex(1)
        elif self.transect.boat_vel.gga_vel.gps_diff_qual_filter == 4:
            self.combo_gps_qual.setCurrentIndex(2)
        else:
            self.combo_gps_qual.setCurrentIndex(0)

        # Set altitude filter from transect data
        index = self.combo_gps_altitude.findText(self.transect.boat_vel.gga_vel.gps_altitude_filter,
                                                 QtCore.Qt.MatchFixedString)
        self.combo_gps_altitude.setCurrentIndex(index)

        # Set hdop filter from transect data
        index = self.combo_gps_hdop.findText(self.transect.boat_vel.gga_vel.gps_HDOP_filter, QtCore.Qt.MatchFixedString)
        self.combo_gps_hdop.setCurrentIndex(index)

        # Set smooth filter from transect data
        if self.transect.boat_vel.gga_vel.smooth_filter == 'Off':
            self.combo_gps_other.setCurrentIndex(0)
        elif self.transect.boat_vel.gga_vel.smooth_filter == 'On':
            self.combo_gps_other.setCurrentIndex(1)

        # Display content
        self.idx = 0
        self.update_gps_table(old_discharge=self.meas.discharge, new_discharge=self.meas.discharge)
        self.gps_plots()
        self.gps_comments_messages()

    def update_gps_table(self, old_discharge, new_discharge):
        """Updates the gps table with new or reprocessed data.

        Parameters
        ----------
        old_discharge: list
            List of objects of QComp with previous settings
        new_discharge: list
            List of objects of QComp with new settings
        """

        with self.wait_cursor():
            # Set tbl variable
            tbl = self.table_gps

            # Populate each row
            for row in range(tbl.rowCount()):
                # Identify transect associated with the row
                transect_id = self.checked_transects_idx[row]
                transect = self.meas.transects[transect_id]
                valid_data = transect.boat_vel.gga_vel.valid_data
                num_ensembles = len(valid_data[0,:])
                if transect.boat_vel.gga_vel is not None:
                    num_invalid_gga = np.nansum(np.logical_not(valid_data[0, :]))
                    num_altitude_invalid = np.nansum(np.logical_not(valid_data[3, :]))
                    num_quality_invalid = np.nansum(np.logical_not(valid_data[2, :]))
                    num_hdop_invalid = np.nansum(np.logical_not(valid_data[5, :]))
                    sats = np.copy(transect.gps.num_sats_ens)
                    if np.nansum(sats) == 0:
                        num_sat_changes = -1
                    else:
                        sats = sats[np.logical_not(np.isnan(sats))]
                        diff_sats = np.diff(sats)
                        num_sat_changes = np.nansum(np.logical_not(diff_sats == 0))
                else:
                    num_invalid_gga = -1
                    num_altitude_invalid = -1
                    num_quality_invalid = -1
                    num_hdop_invalid = -1
                if transect.boat_vel.vtg_vel is not None:
                    num_invalid_vtg = np.nansum(np.logical_not(transect.boat_vel.vtg_vel.valid_data[0, :]))
                else:
                    num_invalid_vtg = -1

                num_other_invalid = np.nansum(np.logical_not(valid_data[4, :]))

                # File/transect name
                col = 0
                item = QtWidgets.QTableWidgetItem(transect.file_name[:-4])
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Total number of ensembles
                col += 1
                item = '{:5d}'.format(num_ensembles)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of ensembles with invalid gga
                col += 1
                if num_invalid_gga > 0:
                    item = '{:3.2f}'.format((num_invalid_gga / num_ensembles) * 100.)
                else:
                    item = 'N/A'
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of ensembles with invalid vtg
                col += 1
                if num_invalid_vtg >= 0:
                    item = '{:3.2f}'.format((num_invalid_vtg / num_ensembles) * 100.)
                else:
                    item = 'N/A'
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of ensembles with invalid quality
                col += 1
                if num_quality_invalid >= 0:
                    item = '{:3.2f}'.format((num_quality_invalid / num_ensembles) * 100.)
                else:
                    item = 'N/A'
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent ensembles with invalid altitude
                col += 1
                if num_altitude_invalid >= 0:
                    item = '{:3.2f}'.format((num_altitude_invalid / num_ensembles) * 100.)
                else:
                    item = 'N/A'
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent ensembles with invalid HDOP
                col += 1
                if num_hdop_invalid >= 0:
                    item = '{:3.2f}'.format((num_hdop_invalid / num_ensembles) * 100.)
                else:
                    item = 'N/A'
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of ensembles with satellite changes
                col += 1
                if num_sat_changes >= 0:
                    item = '{:3.2f}'.format((num_sat_changes / num_ensembles) * 100.)
                else:
                    item = 'N/A'
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent other filter
                col += 1
                if num_other_invalid >= 0:
                    item = '{:3.2f}'.format((num_other_invalid / num_ensembles) * 100.)
                else:
                    item = 'N/A'
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge before changes
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(old_discharge[transect_id].total * self.units['Q'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge after changes
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(new_discharge[transect_id].total * self.units['Q'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent change in discharge
                col += 1
                per_change = ((new_discharge[transect_id].total - old_discharge[transect_id].total)
                              / old_discharge[transect_id].total) * 100
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(per_change)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                self.table_gps.item(row, 0).setFont(self.font_normal)

            # Set selected file to bold font
            self.table_gps.item(self.idx, 0).setFont(self.font_bold)

            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

            self.gps_comments_messages()

    def gps_plots(self):
        """Creates graphics for GPS tab.

        Parameters
        ----------
        idx: int
            Index of the test to be plotted.
        """

        with self.wait_cursor():
            # Set all filenames to normal font
            nrows = len(self.checked_transects_idx)

            # Determine transect selected
            transect_id = self.checked_transects_idx[self.idx]
            self.transect = self.meas.transects[transect_id]
            self.invalid_gps = np.logical_not(self.transect.boat_vel.gga_vel.valid_data)

            for row in range(nrows):
                self.table_gps.item(row, 0).setFont(self.font_normal)

            # Set selected file to bold font
            self.table_gps.item(self.idx, 0).setFont(self.font_bold)
            # Update plots
            self.gps_shiptrack()
            self.gps_boat_speed()
            self.gps_filter_plots()

    def gps_shiptrack(self):
        """Creates shiptrack plot for data in transect.
        """

        # If the canvas has not been previously created, create the canvas and add the widget.
        if not hasattr(self, 'gps_shiptrack_canvas'):
            # Create the canvas
            self.gps_shiptrack_canvas = MplCanvas(parent=self.graph_gps_st, width=4, height=4, dpi=80)
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_gps_st)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.gps_shiptrack_canvas)

        # Initialize the shiptrack figure and assign to the canvas
        self.gps_shiptrack_fig = Shiptrack(canvas=self.gps_shiptrack_canvas)
        # Create the figure with the specified data
        self.gps_shiptrack_fig.create(transect=self.transect,
                                     units=self.units,
                                     cb=True,
                                     cb_bt=self.cb_gps_bt,
                                     cb_gga=self.cb_gps_gga,
                                     cb_vtg=self.cb_gps_vtg,
                                     cb_vectors=self.cb_gps_vectors,
                                     invalid_gps=self.invalid_gps)

        # Draw canvas
        self.gps_shiptrack_canvas.draw()

    def gps_boat_speed(self):
        """Creates boat speed plot for data in transect.
        """

        # If the canvas has not been previously created, create the canvas and add the widget.
        if not hasattr(self, 'gps_bottom_canvas'):
            # Create the canvas
            self.gps_bottom_canvas = MplCanvas(parent=self.graph_gps_bottom, width=8, height=2, dpi=80)
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_gps_bottom)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.gps_bottom_canvas)

        # Initialize the boat speed figure and assign to the canvas
        self.gps_bottom_fig = BoatSpeed(canvas=self.gps_bottom_canvas)
        # Create the figure with the specified data
        self.gps_bottom_fig.create(transect=self.transect,
                                  units=self.units,
                                  cb=True,
                                  cb_bt=self.cb_gps_bt,
                                  cb_gga=self.cb_gps_gga,
                                  cb_vtg=self.cb_gps_vtg,
                                  invalid_gps=self.invalid_gps)

        # Draw canvas
        self.gps_bottom_canvas.draw()

    @QtCore.pyqtSlot()
    def gps_radiobutton_control(self):

        with self.wait_cursor():
            if self.sender().isChecked():
                self.gps_filter_plots()

    def gps_filter_plots(self):
        """Creates plots of filter characteristics.
        """

        # If the canvas has not been previously created, create the canvas and add the widget.
        if not hasattr(self, 'gps_top_canvas'):
            # Create the canvas
            self.gps_top_canvas = MplCanvas(parent=self.graph_gps_top, width=8, height=2, dpi=80)
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_gps_top)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.gps_top_canvas)

        # Initialize the boat speed figure and assign to the canvas
        self.gps_top_fig = GPSFilters(canvas=self.gps_top_canvas)

        # Create the figure with the specified data
        if self.rb_gps_quality.isChecked():
            self.gps_top_fig.create(transect=self.transect,
                                   units=self.units, selected='quality')
        elif self.rb_gps_altitude.isChecked():
            self.gps_top_fig.create(transect=self.transect,
                                   units=self.units, selected='altitude')
        elif self.rb_gps_hdop.isChecked():
            self.gps_top_fig.create(transect=self.transect,
                                   units=self.units, selected='hdop')
        elif self.rb_gps_other.isChecked():
            self.gps_top_fig.create(transect=self.transect,
                                   units=self.units, selected='other')
        elif self.rb_gps_sats.isChecked():
            self.gps_top_fig.create(transect=self.transect,
                                   units=self.units, selected='sats')

        # Draw canvas
        self.gps_top_canvas.draw()

    def gps_table_clicked(self, row, column):
        """Changes plotted data to the transect of the transect clicked.

        Parameters
        ----------
        row: int
            Row clicked by user
        column: int
            Column clicked by user
        """

        if column == 0:
            self.idx = row
            self.gps_plots()

    @QtCore.pyqtSlot()
    def gps_plot_change(self):
        """Coordinates changes in what references should be displayed in the boat speed and shiptrack plots.
        """
        with self.wait_cursor():
            # Shiptrack
            self.gps_shiptrack_fig.change()
            self.gps_shiptrack_canvas.draw()

            # Boat speed
            self.gps_bottom_fig.change()
            self.gps_bottom_canvas.draw()

    def update_gps_tab(self, s):
        """Updates the measurement and bottom track tab (table and graphics) after a change to settings has been made.

        Parameters
        ----------
        s: dict
            Dictionary of all process settings for the measurement
        """

        # Save discharge from previous settings
        old_discharge = copy.deepcopy(self.meas.discharge)

        # Apply new settings
        self.meas.apply_settings(settings=s)

        # Update table
        self.update_gps_table(old_discharge=old_discharge, new_discharge=self.meas.discharge)

        # Update plots
        self.gps_plots()

    @QtCore.pyqtSlot(str)
    def change_quality(self, text):
        """Coordinates user initiated change to the beam settings.

        Parameters
        ----------
        text: str
            User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change settings based on combo box selection
            if text == '1-Autonomous':
                s['ggaDiffQualFilter'] = 1
            elif text == '2-Differential':
                s['ggaDiffQualFilter'] = 2
            elif text == '4+-RTK':
                s['ggaDiffQualFilter'] = 4

            # Update measurement and display
            self.update_gps_tab(s)
            self.change = True

    @QtCore.pyqtSlot(str)
    def change_altitude(self, text):
        """Coordinates user initiated change to the error velocity settings.

         Parameters
         ----------
         text: str
             User selection from combo box
         """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            s['ggaAltitudeFilter'] = text

            if text == 'Manual':
                # If Manual enable the line edit box for user input. Updates are not applied until the user has entered
                # a value in the line edit box.
                self.ed_gps_altitude_threshold.setEnabled(True)
            else:
                # If manual is not selected the line edit box is cleared and disabled and the updates applied.
                self.ed_gps_altitude_threshold.setEnabled(False)
                self.ed_gps_altitude_threshold.setText('')
                self.update_gps_tab(s)
            self.change = True

    @QtCore.pyqtSlot(str)
    def change_hdop(self, text):
        """Coordinates user initiated change to the vertical velocity settings.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            s['GPSHDOPFilter'] = text

            if text == 'Manual':
                # If Manual enable the line edit box for user input. Updates are not applied until the user has entered
                # a value in the line edit box.
                self.ed_gps_hdop_threshold.setEnabled(True)
            else:
                # If manual is not selected the line edit box is cleared and disabled and the updates applied.
                self.ed_gps_hdop_threshold.setEnabled(False)
                self.ed_gps_hdop_threshold.setText('')
                self.update_gps_tab(s)
            self.change = True

    @QtCore.pyqtSlot(str)
    def change_gps_other(self, text):
        """Coordinates user initiated change to the vertical velocity settings.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            if text == 'Off':
                s['GPSSmoothFilter'] = 'Off'
            elif text == 'Smooth':
                s['GPSSmoothFilter'] = 'On'

            # Update measurement and display
            self.update_gps_tab(s)
            self.change = True

    @QtCore.pyqtSlot()
    def change_altitude_threshold(self):
        """Coordinates application of a user specified error velocity threshold.
        """

        with self.wait_cursor():
            # Get threshold and convert to SI units
            threshold = float(self.ed_gps_altitude_threshold.text()) / self.units['L']

            # Get current settings
            s = self.meas.current_settings()
            # Because editingFinished is used if return is pressed and later focus is changed the method could get
            # twice. This line checks to see if there was and actual change.
            if np.abs(threshold - s['ggaAltitudeFilterChange']) > 0.0001:
                # Change settings to manual and the associated threshold
                s['ggaAltitudeFilter'] = 'Manual'
                s['ggaAltitudeFilterChange'] = threshold

                # Update measurement and display
                self.update_gps_tab(s)
                self.change = True

    @QtCore.pyqtSlot()
    def change_hdop_threshold(self):
        """Coordinates application of a user specified vertical velocity threshold.
        """

        with self.wait_cursor():
            # Get threshold and convert to SI units
            threshold = float(self.ed_gps_hdop_threshold.text())

            # Get current settings
            s = self.meas.current_settings()
            # Because editingFinished is used if return is pressed and later focus is changed the method could get
            # twice. This line checks to see if there was and actual change.
            if np.abs(threshold - s['GPSHDOPFilterMax']) > 0.0001:
                # Change settings to manual and the associated threshold
                s['GPSHDOPFilter'] = 'Manual'
                s['GPSHDOPFilterMax'] = threshold

                # Update measurement and display
                self.update_gps_tab(s)
                self.change = True

    def gps_comments_messages(self):
        """Displays comments and messages associated with bottom track filters in Messages tab.
        """

        # Clear comments and messages
        self.display_gps_comments.clear()
        self.display_gps_messages.clear()

        if hasattr(self, 'meas'):
            # Display each comment on a new line
            self.display_gps_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_gps_comments.textCursor().insertText(comment)
                self.display_gps_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_gps_comments.textCursor().insertBlock()

            # Display each message on a new line
            self.display_gps_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.gga_vel['messages']:
                self.display_gps_messages.textCursor().insertText(message[0])
                self.display_gps_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_gps_messages.textCursor().insertBlock()
            for message in self.meas.qa.vtg_vel['messages']:
                self.display_gps_messages.textCursor().insertText(message[0])
                self.display_gps_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_gps_messages.textCursor().insertBlock()

# Depth tab
# =======
    def depth_tab(self):
        """Initialize, setup settings, and display initial data in depth tab.
        """

        # Setup data table
        tbl = self.table_depth
        self.idx = 0
        table_header = [self.tr('Filename'),
                        self.tr('Draft \n' + self.units['label_L']),
                        self.tr('Number or \n Ensembles'),
                        self.tr('Beam 1 \n % Invalid'),
                        self.tr('Beam 2 \n % Invalid'),
                        self.tr('Beam 3 \n % Invalid'),
                        self.tr('Beam 4 \n % Invalid'),
                        self.tr('Vertical \n % Invalid'),
                        self.tr('Depth Sounder \n % Invalid'),
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
        tbl.cellClicked.connect(self.depth_table_clicked)

        # Automatically resize rows and columns
        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        # Initialize checkbox settings top plot and build depth ref combobox options
        self.cb_depth_beam1.setCheckState(QtCore.Qt.Checked)
        self.cb_depth_beam2.setCheckState(QtCore.Qt.Checked)
        self.cb_depth_beam3.setCheckState(QtCore.Qt.Checked)
        self.cb_depth_beam4.setCheckState(QtCore.Qt.Checked)
        depth_ref_options = ['4-Beam Avg']
        if self.meas.transects[self.checked_transects_idx[0]].depths.vb_depths is not None:
            self.cb_depth_vert.setCheckState(QtCore.Qt.Checked)
            depth_ref_options.append('Comp 4-Beam Preferred')
            depth_ref_options.append('Vertical')
            depth_ref_options.append('Comp Vertical Preferred')
        else:
            self.cb_depth_vert.setEnabled(False)
            self.cb_depth_vert_cs.setEnabled(False)
        if self.meas.transects[self.checked_transects_idx[0]].depths.ds_depths is not None:
            self.cb_depth_ds.setCheckState(QtCore.Qt.Checked)
            depth_ref_options.append('Depth Sounder')
            depth_ref_options.append('Comp DS Preferred')
        else:
            self.cb_depth_ds.setEnabled(False)
            self.cb_depth_ds_cs.setEnabled(False)

        # Initialize checkbox settings bottom plot
        self.cb_depth_4beam_cs.setCheckState(QtCore.Qt.Unchecked)
        self.cb_depth_final_cs.setCheckState(QtCore.Qt.Checked)
        self.cb_depth_vert_cs.setCheckState(QtCore.Qt.Unchecked)
        self.cb_depth_ds_cs.setCheckState(QtCore.Qt.Unchecked)

        # Connect top plot variable checkboxes
        self.cb_depth_beam1.stateChanged.connect(self.depth_top_plot_change)
        self.cb_depth_beam2.stateChanged.connect(self.depth_top_plot_change)
        self.cb_depth_beam3.stateChanged.connect(self.depth_top_plot_change)
        self.cb_depth_beam4.stateChanged.connect(self.depth_top_plot_change)
        self.cb_depth_vert.stateChanged.connect(self.depth_top_plot_change)
        self.cb_depth_ds.stateChanged.connect(self.depth_top_plot_change)

        # Connect bottom plot variable checkboxes
        self.cb_depth_4beam_cs.stateChanged.connect(self.depth_bottom_plot_change)
        self.cb_depth_final_cs.stateChanged.connect(self.depth_bottom_plot_change)
        self.cb_depth_vert_cs.stateChanged.connect(self.depth_bottom_plot_change)
        self.cb_depth_ds_cs.stateChanged.connect(self.depth_bottom_plot_change)

        # Connect options
        self.combo_depth_ref.addItems(depth_ref_options)
        self.combo_depth_ref.currentIndexChanged[str].connect(self.change_ref)
        self.combo_depth_avg.currentIndexChanged[str].connect(self.change_avg_method)
        self.combo_depth_filter.currentIndexChanged[str].connect(self.change_filter)

        # Transect selected for display
        self.transect = self.meas.transects[self.checked_transects_idx[0]]
        depth_ref_selected = self.transect.depths.selected
        depth_composite = self.transect.depths.composite

        # Set depth reference
        if depth_ref_selected == 'bt_depths':
            if depth_composite == 'On':
                self.combo_depth_ref.setCurrentIndex(1)
            else:
                self.combo_depth_ref.setCurrentIndex(0)
        elif depth_ref_selected == 'vb_depths':
            if depth_composite == 'On':
                self.combo_depth_ref.setCurrentIndex(3)
            else:
                self.combo_depth_ref.setCurrentIndex(2)
        elif depth_ref_selected == 'ds_depths':
            if depth_composite == 'On':
                self.combo_depth_ref.setCurrentIndex(5)
            else:
                self.combo_depth_ref.setCurrentIndex(4)

        # Set depth average method
        depths_selected = getattr(self.meas.transects[self.checked_transects_idx[0]].depths, depth_ref_selected)
        if depths_selected.avg_method == 'IDW':
            self.combo_depth_avg.setCurrentIndex(0)
        else:
            self.combo_depth_avg.setCurrentIndex(1)

        # Set depth filter method
        if depths_selected.filter_type == 'Smooth':
            self.combo_depth_filter.setCurrentIndex(1)
        elif depths_selected.filter_type == 'TRDI':
            self.combo_depth_filter.setCurrentIndex(2)
        else:
            self.combo_depth_filter.setCurrentIndex(0)

        # Display content
        self.update_depth_table(old_discharge=self.meas.discharge, new_discharge=self.meas.discharge)
        self.depth_plots()
        self.depth_comments_messages()

    def update_depth_table(self, old_discharge, new_discharge):
        """Updates the depth table with new or reprocessed data.

        Parameters
        ----------
        old_discharge: list
            List of objects of QComp with previous settings
        new_discharge: list
            List of objects of QComp with new settings
        """

        with self.wait_cursor():
            # Set tbl variable
            tbl = self.table_depth

            # Populate each row
            for row in range(tbl.rowCount()):
                # Identify transect associated with the row
                transect_id = self.checked_transects_idx[row]
                transect = self.meas.transects[transect_id]
                valid_beam_data = transect.depths.bt_depths.valid_beams
                if transect.depths.vb_depths is not None:
                    valid_vert_beam = transect.depths.vb_depths.valid_beams
                else:
                    valid_vert_beam = None
                if transect.depths.ds_depths is not None:
                    valid_ds_beam = transect.depths.ds_depths.valid_beams
                else:
                    valid_ds_beam = None

                num_ensembles = len(valid_beam_data[0,:])

                # File/transect name
                col = 0
                item = QtWidgets.QTableWidgetItem(transect.file_name[:-4])
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                col += 1
                item = '{:5.2f}'.format(transect.depths.bt_depths.draft_use_m * self.units['L'])
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Total number of ensembles
                col += 1
                item = '{:5d}'.format(num_ensembles)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of invalid depths in beam 1
                col += 1
                item = '{:3.2f}'.format(((num_ensembles - np.nansum(valid_beam_data[0, :])) / num_ensembles) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of invalid depths in beam 2
                col += 1
                item = '{:3.2f}'.format(((num_ensembles - np.nansum(valid_beam_data[1, :])) / num_ensembles) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of invalid depths in beam 3
                col += 1
                item = '{:3.2f}'.format(((num_ensembles - np.nansum(valid_beam_data[2, :])) / num_ensembles) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of invalid depths in beam 4
                col += 1
                item = '{:3.2f}'.format(((num_ensembles - np.nansum(valid_beam_data[3, :])) / num_ensembles) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of invalid depths in vertical beam
                col += 1
                if valid_vert_beam is not None:
                    item = '{:3.2f}'.format(((num_ensembles - np.nansum(valid_vert_beam)) / num_ensembles) * 100.)
                else:
                    item = 'N/A'
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent of invalid depths in depth sounder
                col += 1
                if valid_ds_beam is not None:
                    item = '{:3.2f}'.format(((num_ensembles - np.nansum(valid_ds_beam)) / num_ensembles) * 100.)
                else:
                    item = 'N/A'
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge before changes
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(old_discharge[transect_id].total * self.units['Q'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge after changes
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(new_discharge[transect_id].total * self.units['Q'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent change in discharge
                col += 1
                per_change = ((new_discharge[transect_id].total - old_discharge[transect_id].total)
                              / old_discharge[transect_id].total) * 100
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(per_change)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                tbl.item(row, 0).setFont(self.font_normal)

            # Set selected file to bold font
            tbl.item(self.idx, 0).setFont(self.font_bold)

            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

    def depth_plots(self):
        """Creates graphics for depth tab.
        """

        with self.wait_cursor():
            # Set all filenames to normal font
            nrows = len(self.checked_transects_idx)

            # Determine transect selected
            transect_id = self.checked_transects_idx[self.idx]
            self.transect = self.meas.transects[transect_id]

            for row in range(nrows):
                self.table_depth.item(row, 0).setFont(self.font_normal)

            # Set selected file to bold font
            self.table_depth.item(self.idx, 0).setFont(self.font_bold)

            # Update plots
            self.depth_top_plot()
            self.depth_bottom_plot()

    def depth_top_plot(self):
        """Creates top plot containing individual beam depths.
        """

        # If the canvas has not been previously created, create the canvas and add the widget.
        if not hasattr(self, 'depth_top_canvas'):
            # Create the canvas
            self.depth_top_canvas = MplCanvas(parent=self.graph_depth_beams, width=8, height=2, dpi=80)
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_depth_beams)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.depth_top_canvas)

        # Initialize the top figure and assign to the canvas
        self.depth_top_fig = BeamDepths(canvas=self.depth_top_canvas)
        # Create the figure with the specified data
        self.depth_top_fig.create(transect=self.transect,
                                  units=self.units,
                                  cb_beam1=self.cb_depth_beam1,
                                  cb_beam2=self.cb_depth_beam2,
                                  cb_beam3=self.cb_depth_beam3,
                                  cb_beam4=self.cb_depth_beam4,
                                  cb_vert=self.cb_depth_vert,
                                  cb_ds=self.cb_depth_ds)

        # Draw canvas
        self.depth_top_canvas.draw()

    def depth_bottom_plot(self):
        """Creates bottom plot containing average cross section.
        """

        # If the canvas has not been previously created, create the canvas and add the widget.
        if not hasattr(self, 'depth_bottom_canvas'):
            # Create the canvas
            self.depth_bottom_canvas = MplCanvas(parent=self.graph_depth_cs, width=8, height=2, dpi=80)
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_depth_cs)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.depth_bottom_canvas)

        # Initialize the bottom figure and assign to the canvas
        self.depth_bottom_fig = CrossSection(canvas=self.depth_bottom_canvas)
        # Create the figure with the specified data
        self.depth_bottom_fig.create(transect=self.transect,
                                  units=self.units,
                                  cb_beam_cs=self.cb_depth_4beam_cs,
                                  cb_vert_cs=self.cb_depth_vert_cs,
                                  cb_ds_cs=self.cb_depth_ds_cs,
                                  cb_final_cs=self.cb_depth_final_cs)

        # Draw canvas
        self.depth_bottom_canvas.draw()

    def depth_table_clicked(self, row, column):
        """Changes plotted data to the transect of the transect clicked or allows changing of the draft.

        Parameters
        ----------
        row: int
            Row clicked by user
        column: int
            Column clicked by user
        """

        # Change transect plotted
        if column == 0:
            self.idx = row
            self.depth_plots()

        # Change draft
        if column == 1:
            # Intialize dialog
            draft_dialog = Draft(self)
            draft_dialog.draft_units.setText(self.units['label_L'])
            draft_entered = draft_dialog.exec_()
            # If data entered.
            with self.wait_cursor():
                if draft_entered:
                    draft = float(draft_dialog.ed_draft.text())
                    draft = draft / self.units['L']
                    # Apply change to selected or all transects
                    if draft_dialog.rb_all.isChecked():
                        self.meas.change_draft(draft=draft)
                    else:
                        self.meas.change_draft(draft=draft, transect_idx=self.checked_transects_idx[row])

                    # Update depth tab
                    s = self.meas.current_settings()
                    self.update_depth_tab(s)

    def update_depth_tab(self, s):
        """Updates the depth tab (table and graphics) after a change to settings has been made.

        Parameters
        ----------
        s: dict
            Dictionary of all process settings for the measurement
        """

        # Save discharge from previous settings
        old_discharge = copy.deepcopy(self.meas.discharge)

        # Apply new settings
        self.meas.apply_settings(settings=s)

        # Update table
        self.update_depth_table(old_discharge=old_discharge, new_discharge=self.meas.discharge)

        # Update plots
        self.depth_plots()

        self.depth_comments_messages()

    @QtCore.pyqtSlot()
    def depth_top_plot_change(self):
        """Coordinates changes in user selected data to be displayed in the top plot.
        """
        with self.wait_cursor():
            self.depth_top_fig.change()
            self.depth_top_canvas.draw()

    @QtCore.pyqtSlot()
    def depth_bottom_plot_change(self):
        """Coordinates changes in user selected data to be displayed in the bottom plot.
        """
        with self.wait_cursor():
            self.depth_bottom_fig.change()
            self.depth_bottom_canvas.draw()

    @QtCore.pyqtSlot(str)
    def change_ref(self, text):
        """Coordinates user initiated change to the beam settings.

        Parameters
        ----------
        text: str
            User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change settings based on combo box selection
            if text == '4-Beam Avg':
                s['depthReference'] = 'bt_depths'
                s['depthComposite'] = 'Off'
            elif text == 'Comp 4-Beam Preferred':
                s['depthReference'] = 'bt_depths'
                s['depthComposite'] = 'On'
            elif text == 'Vertical':
                s['depthReference'] = 'vb_depths'
                s['depthComposite'] = 'Off'
            elif text == 'Comp Vertical Preferred':
                s['depthReference'] = 'vb_depths'
                s['depthComposite'] = 'On'
            elif text == 'Depth Sounder':
                s['depthReference'] = 'ds_depths'
                s['depthComposite'] = 'Off'
            elif text == 'Comp DS Preferred':
                s['depthReference'] = 'ds_depths'
                s['depthComposite'] = 'On'

            # Update measurement and display
            self.update_depth_tab(s)
            self.change = True

    @QtCore.pyqtSlot(str)
    def change_filter(self, text):
        """Coordinates user initiated change to the beam settings.

    Parameters
    ----------
    text: str
        User selection from combo box
    """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()
            s['depthFilterType'] = text

            # Update measurement and display
            self.update_depth_tab(s)
            self.change = True

    @QtCore.pyqtSlot(str)
    def change_avg_method(self, text):
        """Coordinates user initiated change to the beam settings.

    Parameters
    ----------
    text: str
        User selection from combo box
    """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()
            s['depthAvgMethod'] = text

            # Update measurement and display
            self.update_depth_tab(s)
            self.change = True

    def depth_comments_messages(self):
        """Displays comments and messages associated with bottom track filters in Messages tab.
        """

        # Clear comments and messages
        self.display_depth_comments.clear()
        self.display_depth_messages.clear()

        if hasattr(self, 'meas'):
            # Display each comment on a new line
            self.display_depth_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_depth_comments.textCursor().insertText(comment)
                self.display_depth_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_depth_comments.textCursor().insertBlock()

            # Display each message on a new line
            self.display_depth_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.depths['messages']:
                self.display_depth_messages.textCursor().insertText(message[0])
                self.display_depth_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_depth_messages.textCursor().insertBlock()

# WT tab
# ======
    def wt_tab(self):
        """Initialize, setup settings, and display initial data in water track tab.
        """

        # Setup data table
        tbl = self.table_wt
        table_header = [self.tr('Filename'),
                        self.tr('Number of \n Depth Cells'),
                        self.tr('Beam \n % <4'),
                        self.tr('Total \n % Invalid'),
                        self.tr('Orig Data \n % Invalid'),
                        self.tr('<4 Beam \n % Invalid'),
                        self.tr('Error Vel \n % Invalid'),
                        self.tr('Vert Vel \n % Invalid'),
                        self.tr('Other \n % Invalid'),
                        self.tr('SNR \n % Invalid'),
                        self.tr('Discharge \n Previous ' + self.units['label_Q']),
                        self.tr('Discharge \n Now ' + self.units['label_Q']),
                        self.tr('Discharge \n % Change')]
        ncols = len(table_header)
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.cellClicked.connect(self.wt_table_clicked)

        # Automatically resize rows and columns
        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        # Initialize checkbox settings for boat reference
        self.cb_wt_bt.setCheckState(QtCore.Qt.Checked)
        self.cb_wt_gga.setCheckState(QtCore.Qt.Unchecked)
        self.cb_wt_vtg.setCheckState(QtCore.Qt.Unchecked)
        selected = self.meas.transects[self.checked_transects_idx[0]].boat_vel.selected
        if selected == 'gga_vel':
            self.cb_wt_gga.setCheckState(QtCore.Qt.Checked)
        elif selected == 'vtg_vel':
            self.cb_wt_vtg.setCheckState(QtCore.Qt.Checked)

        self.cb_wt_vectors.setCheckState(QtCore.Qt.Checked)

        # Connect plot variable checkboxes
        self.cb_wt_bt.stateChanged.connect(self.wt_plot_change)
        self.cb_wt_gga.stateChanged.connect(self.wt_plot_change)
        self.cb_wt_vtg.stateChanged.connect(self.wt_plot_change)
        self.cb_wt_vectors.stateChanged.connect(self.wt_plot_change)

        # Connect radio buttons
        self.rb_wt_beam.toggled.connect(self.wt_radiobutton_control)
        self.rb_wt_error.toggled.connect(self.wt_radiobutton_control)
        self.rb_wt_vert.toggled.connect(self.wt_radiobutton_control)
        if self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer == 'SonTek':
            self.rb_wt_snr.setEnabled(True)
            self.combo_wt_snr.setEnabled(True)
            self.rb_wt_snr.toggled.connect(self.wt_radiobutton_control)
        else:
            self.rb_wt_snr.setEnabled(False)
            self.combo_wt_snr.setEnabled(False)

        self.rb_wt_speed.toggled.connect(self.wt_radiobutton_control)
        self.rb_wt_contour.toggled.connect(self.wt_radiobutton_control)

        # Connect manual entry
        self.ed_wt_error_vel_threshold.editingFinished.connect(self.change_wt_error_vel_threshold)
        self.ed_wt_vert_vel_threshold.editingFinished.connect(self.change_wt_vert_vel_threshold)

        # Connect filters
        self.ed_wt_excluded_dist.editingFinished.connect(self.change_wt_excluded_dist)
        self.combo_wt_3beam.currentIndexChanged[str].connect(self.change_wt_beam)
        self.combo_wt_error_velocity.currentIndexChanged[str].connect(self.change_wt_error)
        self.combo_wt_vert_velocity.currentIndexChanged[str].connect(self.change_wt_vertical)
        self.combo_wt_snr.currentIndexChanged[str].connect(self.change_wt_snr)

        # Transect selected for display
        self.transect = self.meas.transects[self.checked_transects_idx[0]]
        self.idx = 0
        self.update_wt_table(old_discharge=self.meas.discharge, new_discharge=self.meas.discharge)

        # Set beam filter from transect data
        if self.transect.w_vel.beam_filter < 0:
            self.combo_wt_3beam.setCurrentIndex(0)
        elif self.transect.w_vel.beam_filter == 3:
            self.combo_wt_3beam.setCurrentIndex(1)
        elif self.transect.w_vel.beam_filter == 4:
            self.combo_wt_3beam.setCurrentIndex(2)
        else:
            self.combo_wt_3beam.setCurrentIndex(0)

        # Set excluded distance from transect data
        ex_dist = self.meas.transects[self.checked_transects_idx[0]].w_vel.excluded_dist_m * self.units['L']
        self.ed_wt_excluded_dist.setText('{:2.2f}'.format(ex_dist))

        # Set error velocity filter from transect data
        index = self.combo_wt_error_velocity.findText(self.transect.w_vel.d_filter, QtCore.Qt.MatchFixedString)
        self.combo_wt_error_velocity.setCurrentIndex(index)

        # Set vertical velocity filter from transect data
        index = self.combo_wt_vert_velocity.findText(self.transect.w_vel.w_filter, QtCore.Qt.MatchFixedString)
        self.combo_wt_vert_velocity.setCurrentIndex(index)

        # Set smooth filter from transect data
        if self.transect.w_vel.snr_filter == 'Auto':
            self.combo_wt_snr.setCurrentIndex(0)
        elif self.transect.w_vel.snr_filter == 'Off':
            self.combo_wt_snr.setCurrentIndex(1)

        # Display content

        self.wt_plots()
        self.wt_comments_messages()

    def update_wt_table(self, old_discharge, new_discharge):
        """Updates the bottom track table with new or reprocessed data.

        Parameters
        ----------
        old_discharge: list
            List of objects of QComp with previous settings
        new_discharge: list
            List of objects of QComp with new settings
        """

        with self.wait_cursor():
            # Set tbl variable
            tbl = self.table_wt

            # Populate each row
            for row in range(tbl.rowCount()):
                # Identify transect associated with the row
                transect_id = self.checked_transects_idx[row]
                transect = self.meas.transects[transect_id]
                valid_data = transect.w_vel.valid_data
                useable_cells = transect.w_vel.valid_data[6, :, :]
                num_useable_cells = np.nansum(np.nansum(useable_cells.astype(int)))
                # less_than_4 = np.copy(transect.w_vel.d_mps)
                # less_than_4[np.logical_not(transect.w_vel.valid_data[1, :, :])] = -999
                # not_4beam = np.nansum(np.nansum(np.isnan(less_than_4[useable_cells])))
                wt_temp = copy.deepcopy(transect.w_vel)
                wt_temp.filter_beam(4)
                not_4beam = np.nansum(np.nansum(np.logical_not(wt_temp.valid_data[5, :, :][useable_cells])))
                num_invalid = np.nansum(np.nansum(np.logical_not(valid_data[0, :, :][useable_cells])))
                num_orig_invalid = np.nansum(np.nansum(np.logical_not(valid_data[1, :, :][useable_cells])))
                num_beam_invalid = np.nansum(np.nansum(np.logical_not(valid_data[5, :, :][useable_cells])))
                num_error_invalid = np.nansum(np.nansum(np.logical_not(valid_data[2, :, :][useable_cells])))
                num_vert_invalid = np.nansum(np.nansum(np.logical_not(valid_data[3, :, :][useable_cells])))
                num_other_invalid = np.nansum(np.nansum(np.logical_not(valid_data[4, :, :][useable_cells])))
                num_snr_invalid = np.nansum(np.nansum(np.logical_not(valid_data[7, :, :][useable_cells])))

                # File/transect name
                col = 0
                item = QtWidgets.QTableWidgetItem(transect.file_name[:-4])
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                tbl.item(row, 0).setFont(self.font_normal)

                # Total number of depth cells
                col += 1
                item = '{:7d}'.format(num_useable_cells)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Less than 4 beams
                col += 1
                item = '{:3.2f}'.format((not_4beam / num_useable_cells) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Invalid total
                col += 1
                item = '{:3.2f}'.format((num_invalid / num_useable_cells) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Invalid original data
                col += 1
                item = '{:3.2f}'.format((num_orig_invalid / num_useable_cells) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Invalid 3 beam
                col += 1
                item = '{:3.2f}'.format((num_beam_invalid / num_useable_cells) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Error velocity invalid
                col += 1
                item = '{:3.2f}'.format((num_error_invalid / num_useable_cells) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Vertical velocity invalid
                col += 1
                item = '{:3.2f}'.format((num_vert_invalid / num_useable_cells) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Other
                col += 1
                item = '{:3.2f}'.format((num_other_invalid / num_useable_cells) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # SNR
                col += 1
                item = '{:3.2f}'.format((num_snr_invalid / num_useable_cells) * 100.)
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge before changes
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(
                    '{:8.1f}'.format(old_discharge[transect_id].total * self.units['Q'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Discharge after changes
                col += 1
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(
                    '{:8.1f}'.format(new_discharge[transect_id].total * self.units['Q'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

                # Percent change in discharge
                col += 1
                per_change = ((new_discharge[transect_id].total - old_discharge[transect_id].total)
                              / old_discharge[transect_id].total) * 100
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(per_change)))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Set selected file to bold font
            tbl.item(self.idx, 0).setFont(self.font_bold)

            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

            self.wt_comments_messages()

    def wt_plots(self):
        """Creates graphics for WT tab.
        """

        with self.wait_cursor():
            # Set all filenames to normal font
            nrows = len(self.checked_transects_idx)
            for nrow in range(nrows):
                self.table_wt.item(nrow, 0).setFont(self.font_normal)

            # Set selected file to bold font
            self.table_wt.item(self.idx, 0).setFont(self.font_bold)

            # Determine transect selected
            transect_id = self.checked_transects_idx[self.idx]
            self.transect = self.meas.transects[transect_id]
            self.invalid_wt = np.logical_not(self.transect.w_vel.valid_data)

            # Update plots
            self.wt_shiptrack()
            self.wt_water_speed_contour()
            self.wt_filter_plots()

    def wt_shiptrack(self):
        """Creates shiptrack plot for data in transect.
        """

        # If the canvas has not been previously created, create the canvas and add the widget.
        if not hasattr(self, 'wt_shiptrack_canvas'):
            # Create the canvas
            self.wt_shiptrack_canvas = MplCanvas(parent=self.graph_wt_st, width=4, height=4, dpi=80)
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_wt_st)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.wt_shiptrack_canvas)

        # Initialize the shiptrack figure and assign to the canvas
        self.wt_shiptrack_fig = Shiptrack(canvas=self.wt_shiptrack_canvas)
        # Create the figure with the specified data
        self.wt_shiptrack_fig.create(transect=self.transect,
                                     units=self.units,
                                     cb=True,
                                     cb_bt=self.cb_wt_bt,
                                     cb_gga=self.cb_wt_gga,
                                     cb_vtg=self.cb_wt_vtg,
                                     cb_vectors=self.cb_wt_vectors)
            # ,
            #                          invalid_wt=self.invalid_wt)

        # Draw canvas
        self.wt_shiptrack_canvas.draw()

    def wt_water_speed_contour(self):
        """Creates boat speed plot for data in transect.
        """

        # If the canvas has not been previously created, create the canvas and add the widget.
        if not hasattr(self, 'wt_bottom_canvas'):
            # Create the canvas
            self.wt_bottom_canvas = MplCanvas(parent=self.graph_wt_bottom, width=10, height=2, dpi=80)
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_wt_bottom)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.wt_bottom_canvas)

        # Initialize the boat speed figure and assign to the canvas
        self.wt_bottom_fig = WTContour(canvas=self.wt_bottom_canvas)
        # Create the figure with the specified data
        self.wt_bottom_fig.create(transect=self.transect,
                                  units=self.units)

        # Draw canvas
        self.wt_bottom_canvas.draw()

    @QtCore.pyqtSlot()
    def wt_radiobutton_control(self):

        with self.wait_cursor():
            if self.sender().isChecked():
                self.wt_filter_plots()

    def wt_filter_plots(self):
        """Creates plots of filter characteristics.
        """

        # If the canvas has not been previously created, create the canvas and add the widget.
        if not hasattr(self, 'wt_top_canvas'):
            # Create the canvas
            self.wt_top_canvas = MplCanvas(parent=self.graph_wt_top, width=10, height=2, dpi=80)
            # Assign layout to widget to allow auto scaling
            layout = QtWidgets.QVBoxLayout(self.graph_wt_top)
            # Adjust margins of layout to maximize graphic area
            layout.setContentsMargins(1, 1, 1, 1)
            # Add the canvas
            layout.addWidget(self.wt_top_canvas)

        if self.rb_wt_contour.isChecked():
            # Initialize the contour plot
            # Initialize the water filters figure and assign to the canvas
            self.wt_top_fig = WTContour(canvas=self.wt_top_canvas)
            # Determine invalid data based on depth, nav, and wt
            depth_valid = getattr(self.transect.depths, self.transect.depths.selected).valid_data
            boat_valid = getattr(self.transect.boat_vel, self.transect.boat_vel.selected).valid_data[0, :]
            invalid_ens = np.logical_not(np.logical_and(depth_valid, boat_valid))
            valid_data = self.transect.w_vel.valid_data[0, :, :]
            valid_data[:, invalid_ens] = False
            # Create the figure with the specified data
            self.wt_top_fig.create(transect=self.transect,
                                      units=self.units,
                                      invalid_data=np.logical_not(self.transect.w_vel.valid_data[0, :, :]))
        else:
            # Initialize the wt filters plot
            self.wt_top_fig = WTFilters(canvas=self.wt_top_canvas)
            # Create the figure with the specified data
            if self.rb_wt_beam.isChecked():
                self.wt_top_fig.create(transect=self.transect,
                                       units=self.units, selected='beam')
            elif self.rb_wt_error.isChecked():
                self.wt_top_fig.create(transect=self.transect,
                                       units=self.units, selected='error')
            elif self.rb_wt_vert.isChecked():
                self.wt_top_fig.create(transect=self.transect,
                                       units=self.units, selected='vert')
            elif self.rb_wt_speed.isChecked():
                self.wt_top_fig.create(transect=self.transect,
                                       units=self.units, selected='speed')
            elif self.rb_wt_snr.isChecked():
                self.wt_top_fig.create(transect=self.transect,
                                       units=self.units, selected='snr')

        # Draw canvas
        self.wt_top_canvas.draw()

    def wt_table_clicked(self, row, column):
        """Changes plotted data to the transect of the transect clicked.

        Parameters
        ----------
        row: int
            Row clicked by user
        column: int
            Column clicked by user
        """

        if column == 0:
            self.idx = row
            self.wt_plots()

    @QtCore.pyqtSlot()
    def wt_plot_change(self):
        """Coordinates changes in what references should be displayed in the shiptrack plots.
        """

        with self.wait_cursor():
            # Shiptrack
            self.wt_shiptrack_fig.change()
            self.wt_shiptrack_canvas.draw()

    def update_wt_tab(self, s):
        """Updates the measurement and water track tab (table and graphics) after a change to settings has been made.

        Parameters
        ----------
        s: dict
            Dictionary of all process settings for the measurement
        """

        # Save discharge from previous settings
        old_discharge = copy.deepcopy(self.meas.discharge)

        # Apply new settings
        self.meas.apply_settings(settings=s)

        # Update table
        self.update_wt_table(old_discharge=old_discharge, new_discharge=self.meas.discharge)

        # Update plots
        self.wt_plots()

    @QtCore.pyqtSlot(str)
    def change_wt_beam(self, text):
        """Coordinates user initiated change to the beam settings.

        Parameters
        ----------
        text: str
            User selection from combo box
        """

        with self.wait_cursor():

            # Get current settings
            s = self.meas.current_settings()

            if text == 'Auto':
                s['WTbeamFilter'] = -1
            elif text == 'Allow':
                s['WTbeamFilter'] = 3
            elif text == '4-Beam Only':
                s['WTbeamFilter'] = 4

            # Update measurement and display
            self.update_wt_tab(s)
            self.change = True

    @QtCore.pyqtSlot(str)
    def change_wt_error(self, text):
        """Coordinates user initiated change to the error velocity settings.

         Parameters
         ----------
         text: str
             User selection from combo box
         """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            s['WTdFilter'] = text

            if text == 'Manual':
                # If Manual enable the line edit box for user input. Updates are not applied until the user has entered
                # a value in the line edit box.
                self.ed_wt_error_vel_threshold.setEnabled(True)
            else:
                # If manual is not selected the line edit box is cleared and disabled and the updates applied.
                self.ed_wt_error_vel_threshold.setEnabled(False)
                self.ed_wt_error_vel_threshold.setText('')
                self.update_wt_tab(s)
            self.change = True

    @QtCore.pyqtSlot(str)
    def change_wt_vertical(self, text):
        """Coordinates user initiated change to the vertical velocity settings.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            s['WTwFilter'] = text

            if text == 'Manual':
                # If Manual enable the line edit box for user input. Updates are not applied until the user has entered
                # a value in the line edit box.
                self.ed_wt_vert_vel_threshold.setEnabled(True)
            else:
                # If manual is not selected the line edit box is cleared and disabled and the updates applied.
                self.ed_wt_vert_vel_threshold.setEnabled(False)
                self.ed_wt_vert_vel_threshold.setText('')
                self.update_wt_tab(s)
            self.change = True

    @QtCore.pyqtSlot(str)
    def change_wt_snr(self, text):
        """Coordinates user initiated change to the vertical velocity settings.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Get current settings
            s = self.meas.current_settings()

            # Change setting based on combo box selection
            if text == 'Off':
                s['WTsnrFilter'] = 'Off'
            elif text == 'Auto':
                s['WTsnrFilter'] = 'Auto'

            # Update measurement and display
            self.update_wt_tab(s)
            self.change = True

    @QtCore.pyqtSlot()
    def change_wt_error_vel_threshold(self):
        """Coordinates application of a user specified error velocity threshold.
        """

        with self.wait_cursor():
            # Get threshold and convert to SI units
            threshold = float(self.ed_wt_error_vel_threshold.text()) / self.units['V']

            # Get current settings
            s = self.meas.current_settings()
            # Because editingFinished is used if return is pressed and later focus is changed the method could get
            # twice. This line checks to see if there was and actual change.
            if np.abs(threshold - s['WTdFilterThreshold']) > 0.0001:
                # Change settings to manual and the associated threshold
                s['WTdFilter'] = 'Manual'
                s['WTdFilterThreshold'] = threshold

                # Update measurement and display
                self.update_wt_tab(s)
                self.change = True

    @QtCore.pyqtSlot()
    def change_wt_vert_vel_threshold(self):
        """Coordinates application of a user specified vertical velocity threshold.
        """

        with self.wait_cursor():
            # Get threshold and convert to SI units
            threshold = float(self.ed_wt_vert_vel_threshold.text()) / self.units['V']

            # Get current settings
            s = self.meas.current_settings()
            # Because editingFinished is used if return is pressed and later focus is changed the method could get
            # twice. This line checks to see if there was and actual change.
            if np.abs(threshold - s['WTwFilterThreshold']) > 0.0001:
                # Change settings to manual and the associated threshold
                s['WTwFilter'] = 'Manual'
                s['WTwFilterThreshold'] = threshold

                # Update measurement and display
                self.update_wt_tab(s)
                self.change = True

    @QtCore.pyqtSlot()
    def change_wt_excluded_dist(self):
        """Coordinates application of a user specified excluded distance.
        """

        with self.wait_cursor():
            # Get threshold and convert to SI units
            threshold = float(self.ed_wt_excluded_dist.text()) / self.units['L']

            # Get current settings
            s = self.meas.current_settings()
            # Because editingFinished is used if return is pressed and later focus is changed the method could get
            # twice. This line checks to see if there was and actual change.
            if np.abs(threshold - s['WTExcludedDistance']) > 0.0001:
                # Change settings
                s['WTExcludedDistance'] = threshold

                # Update measurement and display
                self.update_wt_tab(s)
                self.change = True

    def wt_comments_messages(self):
        """Displays comments and messages associated with bottom track filters in Messages tab.
        """

        # Clear comments and messages
        self.display_wt_comments.clear()
        self.display_wt_messages.clear()

        if hasattr(self, 'meas'):
            # Display each comment on a new line
            self.display_wt_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_wt_comments.textCursor().insertText(comment)
                self.display_wt_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_wt_comments.textCursor().insertBlock()

            # Display each message on a new line
            self.display_wt_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.w_vel['messages']:
                self.display_wt_messages.textCursor().insertText(message[0])
                self.display_wt_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_wt_messages.textCursor().insertBlock()

# Extrap Tab
# ==========
    def extrap_tab(self):
        """Initializes all of the features on the extrap_tab.
        """

        self.extrap_meas = copy.deepcopy(self.meas)

        self.extrap_index(len(self.checked_transects_idx))
        self.start_bank = None

        # Setup number of points data table
        tbl = self.table_extrap_n_points
        table_header = [self.tr('Z'),
                        self.tr('No. Pts.')]
        ncols = len(table_header)
        nrows = len(self.meas.extrap_fit.norm_data[-1].unit_normalized_z)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.n_points_table()

        # Setup discharge sensitivity table
        tbl = self.table_extrap_qsen
        table_header = [self.tr('Top'),
                        self.tr('Bottom'),
                        self.tr('Exponent'),
                        self.tr('% Diff')]
        ncols = len(table_header)
        nrows = 6
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(table_header)
        tbl.horizontalHeader().setFont(self.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.cellClicked.connect(self.sensitivity_change_fit)
        self.q_sensitivity_table()

        # Setup transect / measurement list table
        tbl = self.table_extrap_fit
        ncols = 1
        nrows = len(self.checked_transects_idx) + 1
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.verticalHeader().hide()
        tbl.horizontalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.cellClicked.connect(self.fit_list_table_clicked)
        self.fit_list_table()

        self.display_current_fit()
        self.set_fit_options()

        # Connect fit options
        self.combo_extrap_fit.currentIndexChanged[str].connect(self.change_fit_method)
        self.combo_extrap_top.currentIndexChanged[str].connect(self.change_top_method)
        self.combo_extrap_bottom.currentIndexChanged[str].connect(self.change_bottom_method)
        self.ed_extrap_exponent.editingFinished.connect(self.change_exponent)

        # Connect display settings
        self.cb_extrap_data.stateChanged.connect(self.extrap_plot)
        self.cb_extrap_surface.stateChanged.connect(self.extrap_plot)
        self.cb_extrap_meas_medians.stateChanged.connect(self.extrap_plot)
        self.cb_extrap_meas_fit.stateChanged.connect(self.extrap_plot)
        self.cb_extrap_trans_medians.stateChanged.connect(self.extrap_plot)
        self.cb_extrap_trans_fit.stateChanged.connect(self.extrap_plot)

        # Connect data settings
        self.combo_extrap_data.currentIndexChanged[str].connect(self.change_data)
        self.ed_extrap_threshold.editingFinished.connect(self.change_threshold)
        self.ed_extrap_subsection.editingFinished.connect(self.change_subsection)
        self.combo_extrap_type.currentIndexChanged[str].connect(self.change_data_type)

        self.extrap_set_data()

        # Cancel and apply buttons
        self.pb_extrap_cancel.clicked.connect(self.cancel_extrap)

        self.extrap_plot()

    def extrap_update(self):

        if self.idx == len(self.meas.extrap_fit.sel_fit) - 1:
            s = self.meas.current_settings()
            self.meas.apply_settings(s)
            self.q_sensitivity_table()
            self.extrap_comments_messages()
            self.change = True

        # Update tab
        self.n_points_table()
        self.set_fit_options()
        self.extrap_plot()

    def extrap_index(self, row):
        """Converts the row value to a transect index.

        Parameters
        ----------
        row: int
            Row selected from the fit list table
        """
        if row > len(self.checked_transects_idx) - 1:
            self.idx = len(self.meas.transects)
        else:
            self.idx = self.checked_transects_idx[row]

    def display_current_fit(self):
        """Displays the extrapolation methods currently used to compute discharge.
        """

        # Display Previous settings
        self.txt_extrap_p_fit.setText(self.meas.extrap_fit.sel_fit[-1].fit_method)
        self.txt_extrap_p_top.setText(self.meas.extrap_fit.sel_fit[-1].top_method)
        self.txt_extrap_p_bottom.setText(self.meas.extrap_fit.sel_fit[-1].bot_method)
        self.txt_extrap_p_exponent.setText('{:6.4f}'.format(self.meas.extrap_fit.sel_fit[-1].exponent))

    def set_fit_options(self):
        """Sets the fit options for the currently selected transect or measurement.
        """

        # Setup fit method
        self.combo_extrap_fit.blockSignals(True)
        if self.meas.extrap_fit.sel_fit[self.idx].fit_method == 'Automatic':
            self.combo_extrap_fit.setCurrentIndex(0)
            self.combo_extrap_top.setEnabled(False)
            self.combo_extrap_bottom.setEnabled(False)
            self.ed_extrap_exponent.setEnabled(False)
        else:
            self.combo_extrap_fit.setCurrentIndex(1)
            self.combo_extrap_top.setEnabled(True)
            self.combo_extrap_bottom.setEnabled(True)
            self.ed_extrap_exponent.setEnabled(True)
        self.combo_extrap_fit.blockSignals(False)

        # Set top method
        self.combo_extrap_top.blockSignals(True)
        if self.meas.extrap_fit.sel_fit[self.idx].top_method == 'Power':
            self.combo_extrap_top.setCurrentIndex(0)
        elif self.meas.extrap_fit.sel_fit[self.idx].top_method == 'Constant':
            self.combo_extrap_top.setCurrentIndex(1)
        else:
            self.combo_extrap_top.setCurrentIndex(2)
        self.combo_extrap_top.blockSignals(False)

        # Set bottom method
        self.combo_extrap_bottom.blockSignals(True)
        if self.meas.extrap_fit.sel_fit[self.idx].bot_method == 'Power':
            self.combo_extrap_bottom.setCurrentIndex(0)
        else:
            self.combo_extrap_bottom.setCurrentIndex(1)
        self.combo_extrap_bottom.blockSignals(False)

        # Set exponent
        self.ed_extrap_exponent.blockSignals(True)
        self.ed_extrap_exponent.setText('{:6.4f}'.format(self.meas.extrap_fit.sel_fit[self.idx].exponent))
        self.ed_extrap_exponent.blockSignals(False)

    def n_points_table(self):
        """Populates the table showing the normalized depth of each layer and how many data points are in each layer.
        """

        # Set table variable
        tbl = self.table_extrap_n_points

        # Get normalized data for transect or measurement selected
        norm_data = self.meas.extrap_fit.norm_data[self.idx]

        # Populate the table row by row substituting standard values if no data exist.
        for row in range(len(norm_data.unit_normalized_z)):
            # Column 0 is normalized depth
            col = 0
            if np.isnan(norm_data.unit_normalized_z[row]):
                value = 1 - row / 20.
            else:
                value = norm_data.unit_normalized_z[row]
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:6.4f}'.format(value)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Column 1 is number of points
            col = 1
            if np.isnan(norm_data.unit_normalized_no[row]):
                value = 0
            else:
                value = norm_data.unit_normalized_no[row]
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.0f}'.format(value)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

    def q_sensitivity_table(self):
        """Populates the discharge sensitivity table.
        """

        # Set table reference
        tbl = self.table_extrap_qsen

        # Get sensitivity data
        q_sen = self.meas.extrap_fit.q_sensitivity

        # Power / Power / 1/6
        row = 0
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem('Power'))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('Power'))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        item = '{:6.4f}'.format(0.1667)
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        item = '{:6.2f}'.format(q_sen.q_pp_per_diff)
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Power / Power / Optimize
        row = 1
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem('Power'))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('Power'))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        item = '{:6.4f}'.format(q_sen.pp_exp)
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        item = '{:6.2f}'.format(q_sen.q_pp_opt_per_diff)
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Constant / No Slip / 1/6
        row = 2
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem('Constant'))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('No Slip'))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        item = '{:6.4f}'.format(0.1667)
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        item = '{:6.2f}'.format(q_sen.q_cns_per_diff)
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Constant / No Slip / Optimize
        row = 3
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem('Constant'))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('No Slip'))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        item = '{:6.4f}'.format(q_sen.ns_exp)
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        item = '{:6.2f}'.format(q_sen.q_cns_opt_per_diff)
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # 3-Point / No Slip / 1/6
        row = 4
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem('3-Point'))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('No Slip'))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        item = '{:6.4f}'.format(0.1667)
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        item = '{:6.2f}'.format(q_sen.q_3p_ns_per_diff)
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # 3-Point / No Slip / Optimize
        row = 5
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem('3-Point'))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('No Slip'))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        item = '{:6.4f}'.format(q_sen.ns_exp)
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        item = '{:6.2f}'.format(q_sen.q_3p_ns_opt_per_diff)
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem(item))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Manually set fit method
        if q_sen.q_man_mean is not None:
            row = tbl.rowCount()
            if row == 6:
                tbl.insertRow(row)
            else:
                row = row - 1
            tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(q_sen.man_top))
            tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, 1, QtWidgets.QTableWidgetItem(q_sen.man_bot))
            tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
            item = '{:6.4f}'.format(q_sen.man_exp)
            tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(item))
            tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
            item = '{:6.2f}'.format(q_sen.q_man_per_diff)
            tbl.setItem(row, 3, QtWidgets.QTableWidgetItem(item))
            tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)
        elif tbl.rowCount() == 7:
            tbl.removeRow(6)

        # Set reference
        if q_sen.q_man_mean is not None:
            self.set_extrap_reference(6)
        elif  np.abs(q_sen.q_pp_per_diff) < 0.00000001:
            self.set_extrap_reference(0)
        elif np.abs(q_sen.q_pp_opt_per_diff) < 0.00000001:
            self.set_extrap_reference(1)
        elif np.abs(q_sen.q_cns_per_diff) < 0.00000001:
            self.set_extrap_reference(2)
        elif np.abs(q_sen.q_cns_opt_per_diff) < 0.00000001:
            self.set_extrap_reference(3)
        elif np.abs(q_sen.q_3p_ns_per_diff) < 0.00000001:
            self.set_extrap_reference(4)
        elif np.abs(q_sen.q_3p_ns_opt_per_diff) < 0.00000001:
            self.set_extrap_reference(5)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def set_extrap_reference(self, reference_row):
        """Sets the discharge sensitivity table to show the selected method as the reference.
        """

        # Get table reference
        tbl = self.table_extrap_qsen

        # Set all data to normal font
        for row in range(tbl.rowCount()):
            for col in range(tbl.columnCount()):
                tbl.item(row, col).setFont(self.font_normal)

        # Set selected file to bold font
        for col in range(tbl.columnCount()):
            tbl.item(reference_row, col).setFont(self.font_bold)

    def fit_list_table(self):
        """Populates the fit list table to show all the checked transects and the composite measurement.
        """

        # Get table reference
        tbl = self.table_extrap_fit

        # Add transects and Measurement to table
        for n in range(len(self.checked_transects_idx)):
            item = self.meas.transects[self.checked_transects_idx[n]].file_name[:-4]
            tbl.setItem(n, 0, QtWidgets.QTableWidgetItem(item))
            tbl.item(n, 0).setFlags(QtCore.Qt.ItemIsEnabled)
            tbl.item(n, 0).setFont(self.font_normal)
        tbl.setItem(len(self.checked_transects_idx), 0, QtWidgets.QTableWidgetItem('Measurement'))
        tbl.item(len(self.checked_transects_idx), 0).setFlags(QtCore.Qt.ItemIsEnabled)

        # Show the Measurement as the initial selection
        tbl.item(len(self.checked_transects_idx), 0).setFont(self.font_bold)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    @QtCore.pyqtSlot(int, int)
    def fit_list_table_clicked(self, selected_row, selected_col):
        with self.wait_cursor():
            # Set all filenames to normal font
            nrows = len(self.checked_transects_idx) + 1

            for row in range(nrows):
                self.table_extrap_fit.item(row, 0).setFont(self.font_normal)

            # Set selected file to bold font
            self.table_extrap_fit.item(selected_row, 0).setFont(self.font_bold)

            self.extrap_index(selected_row)
            self.n_points_table()
            self.set_fit_options()
            self.extrap_plot()

    def extrap_plot(self):
            """Creates extrapolation plot.
            """

            # If the canvas has not been previously created, create the canvas and add the widget.
            if not hasattr(self, 'extrap_canvas'):
                # Create the canvas
                self.extrap_canvas = MplCanvas(parent=self.graph_extrap, width=4, height=4, dpi=80)
                # Assign layout to widget to allow auto scaling
                layout = QtWidgets.QVBoxLayout(self.graph_extrap)
                # Adjust margins of layout to maximize graphic area
                layout.setContentsMargins(1, 1, 1, 1)
                # Add the canvas
                layout.addWidget(self.extrap_canvas)

            # Initialize the figure and assign to the canvas
            self.extrap_fig = ExtrapPlot(canvas=self.extrap_canvas)
            # Create the figure with the specified data
            self.extrap_fig.create(meas = self.meas,
                                   checked = self.checked_transects_idx,
                                   idx=self.idx,
                                   data_type=self.combo_extrap_type.currentText(),
                                   cb_data=self.cb_extrap_data.isChecked(),
                                   cb_surface=self.cb_extrap_surface.isChecked(),
                                   cb_trans_medians=self.cb_extrap_trans_medians.isChecked(),
                                   cb_trans_fit=self.cb_extrap_trans_fit.isChecked(),
                                   cb_meas_medians=self.cb_extrap_meas_medians.isChecked(),
                                   cb_meas_fit=self.cb_extrap_meas_fit.isChecked())

            self.extrap_canvas.draw()

    def extrap_set_data(self):
        if self.meas.extrap_fit.sel_fit[-1].data_type.lower() != 'q':
            self.extrap_set_data_manual()
        elif self.meas.extrap_fit.threshold != 20:
            self.extrap_set_data_manual()
        elif self.meas.extrap_fit.subsection[0] != 0 or self.meas.extrap_fit.subsection[1] != 100:
            self.extrap_set_data_manual()
        else:
            self.extrap_set_data_auto()

    def extrap_set_data_manual(self):
        if self.combo_extrap_data.currentIndex() == 0:
            self.combo_extrap_data.setCurrentIndex(1)
        self.ed_extrap_threshold.setEnabled(True)
        self.ed_extrap_subsection.setEnabled(True)
        self.combo_extrap_type.setEnabled(True)
        self.ed_extrap_threshold.setText('{:3.0f}'.format(self.meas.extrap_fit.threshold))
        self.ed_extrap_subsection.setText('{:.0f}:{:.0f}'.format(self.meas.extrap_fit.subsection[0],
                                                                   self.meas.extrap_fit.subsection[1]))
        if self.meas.extrap_fit.sel_fit[-1].data_type.lower() == 'q':
            self.combo_extrap_type.setCurrentIndex(0)
        else:
            self.combo_extrap_type.setCurrentIndex(1)

    def extrap_set_data_auto(self):
        if self.combo_extrap_data.currentIndex() == 1:
            self.combo_extrap_data.setCurrentIndex(0)
        self.ed_extrap_threshold.setEnabled(False)
        self.ed_extrap_subsection.setEnabled(False)
        self.combo_extrap_type.setEnabled(False)
        self.ed_extrap_threshold.setText('20')
        self.ed_extrap_subsection.setText('0:100')
        self.combo_extrap_type.setCurrentIndex(0)




    @QtCore.pyqtSlot(str)
    def change_data(self, text):
        """Coordinates user initiated change to the data from automatic to manual.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            if text == 'Manual':
                self.ed_extrap_threshold.setEnabled(True)
                self.ed_extrap_subsection.setEnabled(True)
                self.combo_extrap_type.setEnabled(True)
            else:
                self.ed_extrap_threshold.setEnabled(False)
                self.ed_extrap_subsection.setEnabled(False)
                self.combo_extrap_type.setEnabled(False)
                self.ed_extrap_threshold.setText('20')
                self.ed_extrap_subsection.setText('0:100')
                self.combo_extrap_type.setCurrentIndex(0)
                self.meas.extrap_fit.change_data_auto(self.meas.transects)

    @QtCore.pyqtSlot()
    def change_threshold(self):
        """Allows the user to change the threshold and then updates the data and display.
        """

        # If data entered.
        with self.wait_cursor():
            threshold = float(self.ed_extrap_threshold.text())

            if np.abs(threshold - self.meas.extrap_fit.threshold) > 0.0001:
                if threshold >= 0 and threshold <= 100:
                    self.meas.extrap_fit.change_threshold(transects=self.meas.transects,
                                                          data_type=self.meas.extrap_fit.sel_fit[0].data_type,
                                                          threshold=threshold)
                    self.extrap_update()
                else:
                    self.ed_extrap_threshold.setText('{:3.0f}'.format(self.meas.extrap_fit.threshold))

    @QtCore.pyqtSlot()
    def change_subsection(self):
        """Allows the user to change the subsectioning and then updates the data and display.
        """

        # If data entered.
        with self.wait_cursor():
            sub_list = self.ed_extrap_subsection.text().split(':')
            subsection = []
            subsection.append(float(sub_list[0]))
            subsection.append(float(sub_list[1]))
            if np.abs(subsection[0] - self.meas.extrap_fit.subsection[0]) > 0.0001\
                    or np.abs(subsection[1] - self.meas.extrap_fit.subsection[1]) > 0.0001:
                if subsection[0] >= 0 and subsection[0] <= 100 and subsection[1] > subsection[0] and subsection[1] <= 100:
                    self.meas.extrap_fit.change_extents(transects=self.meas.transects,
                                                          data_type=self.meas.extrap_fit.sel_fit[-1].data_type,
                                                          extents=subsection)
                    self.extrap_update()
                else:
                    self.ed_extrap_subsection.setText('{:3.0f}:{:3.0f}'.format(self.meas.extrap_fit.subsection))

    @QtCore.pyqtSlot(str)
    def change_data_type(self, text):
        """Coordinates user initiated change to the data type.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():

            # Change setting based on combo box selection
            data_type = 'q'
            if text == 'Velocity':
                data_type = 'v'

            self.meas.extrap_fit.change_data_type(transects=self.meas.transects, data_type=data_type)

            self.extrap_update()

    @QtCore.pyqtSlot(str)
    def change_fit_method(self, text):
        """Coordinates user initiated changing the fit type.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Change setting based on combo box selection
            self.meas.extrap_fit.change_fit_method(transects=self.meas.transects,
                                                   new_fit_method=text,
                                                   idx=self.idx)

            self.extrap_update()

    @QtCore.pyqtSlot(str)
    def change_top_method(self, text):
        """Coordinates user initiated changing the top method.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Change setting based on combo box selection
            self.meas.extrap_fit.change_fit_method(transects=self.meas.transects,
                                                   new_fit_method='Manual',
                                                   idx=self.idx,
                                                   top=text)

            self.extrap_update()

    @QtCore.pyqtSlot(str)
    def change_bottom_method(self, text):
        """Coordinates user initiated changing the bottom method.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            # Change setting based on combo box selection
            self.meas.extrap_fit.change_fit_method(transects=self.meas.transects,
                                                   new_fit_method='Manual',
                                                   idx=self.idx,
                                                   bot=text)

            self.extrap_update()

    @QtCore.pyqtSlot()
    def change_exponent(self):
        """Coordinates user initiated changing the bottom method.

        Parameters
        ----------
        text: str
         User selection from combo box
        """

        with self.wait_cursor():
            exponent = float(self.ed_extrap_exponent.text())
            # Because editingFinished is used if return is pressed and later focus is changed the method could get
            # twice. This line checks to see if there was and actual change.
            if np.abs(exponent - self.meas.extrap_fit.sel_fit[self.idx].exponent) > 0.00001:
                # Change based on user input
                self.meas.extrap_fit.change_fit_method(transects=self.meas.transects,
                                                       new_fit_method='Manual',
                                                       idx=self.idx,
                                                       exponent=exponent)

                self.extrap_update()

    def sensitivity_change_fit(self, row, col):
        """Changes the fit based on the row in the discharge sensitivity table selected by the user.
        """

        with self.wait_cursor():

            # Get fit settings from table
            top = self.table_extrap_qsen.item(row, 0).text()
            bot = self.table_extrap_qsen.item(row, 1).text()
            exponent = float(self.table_extrap_qsen.item(row, 2).text())

            # Change based on user selection
            self.meas.extrap_fit.change_fit_method(transects=self.meas.transects,
                                                   new_fit_method='Manual',
                                                   idx=self.idx,
                                                   top=top,
                                                   bot=bot,
                                                   exponent=exponent)

            self.extrap_update()

    def cancel_extrap(self):
        self.meas = copy.deepcopy(self.extrap_meas)
        self.extrap_tab()
        self.change = False

    def extrap_comments_messages(self):
        """Displays comments and messages associated with bottom track filters in Messages tab.
        """

        # Clear comments and messages
        self.display_extrap_comments.clear()
        self.display_extrap_messages.clear()

        if hasattr(self, 'meas'):
            # Display each comment on a new line
            self.display_extrap_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                self.display_extrap_comments.textCursor().insertText(comment)
                self.display_extrap_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_extrap_comments.textCursor().insertBlock()

            # Display each message on a new line
            self.display_extrap_messages.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.extrapolation['messages']:
                self.display_extrap_messages.textCursor().insertText(message[0])
                self.display_extrap_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_extrap_messages.textCursor().insertBlock()

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

        # Intialize dialog
        rating_dialog = Rating(self)
        rating_dialog.uncertainty_value.setText('{:4.1f}'.format(self.meas.uncertainty.total_95_user))
        if self.meas.uncertainty.total_95_user < 3:
            rating_dialog.rb_excellent.setChecked(True)
        elif self.meas.uncertainty.total_95_user < 5.01:
            rating_dialog.rb_good.setChecked(True)
        elif self.meas.uncertainty.total_95_user < 8.01:
            rating_dialog.rb_fair.setChecked(True)
        else:
            rating_dialog.rb_poor.setChecked(True)
        rating_entered = rating_dialog.exec_()
        # If data entered.
        with self.wait_cursor():
            if rating_entered:
                if rating_dialog.rb_excellent.isChecked():
                    rating = 'Excellent'
                elif rating_dialog.rb_good.isChecked():
                    rating = 'Good'
                elif rating_dialog.rb_fair.isChecked():
                    rating = 'Fair'
                else:
                    rating = 'Poor'

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
             'processed_discharge': discharge['total_mean'],
             'rating': rating}
        self.processed_data.append(q)

        # Load next pairing
        self.group_idx += 1

        # If all pairings have been processed return control to the function initiating QRev.
        if self.group_idx > len(self.groupings) - 1:
            # Create summary of all processed transects
            for idx in range(len(self.meas.transects)):
                q_trans = {'transect_id': idx,
                           'transect_file': self.meas.transects[idx].file_name[:-4],
                           'start_serial_time': self.meas.transects[idx].date_time.start_serial_time,
                           'end_serial_time': self.meas.transects[idx].date_time.end_serial_time,
                           'duration': self.meas.transects[idx].date_time.transect_duration_sec,
                           'processed_discharge': self.meas.discharge[idx].total}
                self.processed_transects.append(q_trans)
            self.caller.processed_meas = self.processed_data
            self.caller.processed_transects = self.processed_transects
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

        elif tab_idx == 5:
            # Bottom track filters
            self.bt_tab()

        elif tab_idx == 6:
            # GPS filters
            self.gps_tab()

        elif tab_idx == 7:
            # Depth filters
            self.depth_tab()

        elif tab_idx == 8:
            # WT filters
            self.wt_tab()

        elif tab_idx == 9:
            # Extrapolation
            self.extrap_tab()

        # elif tab_idx == 10:
        #     # Edges
        #     self.edges_tab()

    def update_comments (self, tab_idx=None):
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
           self.comments_tab()

        elif tab_idx == 1:
            # Show system tab
            self.systest_comments_messages()

        elif tab_idx == 2:
            # Show compass/pr tab
            self.compass_comments_messages()

        elif tab_idx == 3:
            # Temperature, salinity, speed of sound tab
            self.tempsal_comments_messages()

        elif tab_idx == 4:
            # Moving-bed test tab
            self.mb_comments_messages()

        elif tab_idx == 5:
            # Bottom track filters
            self.bt_comments_messages()

        elif tab_idx == 6:
            # GPS filters
            self.gps_comments_messages()

        elif tab_idx == 7:
            # Depth filters
            self.depth_comments_messages()

        elif tab_idx == 8:
            # WT filters
            self.wt_comments_messages()

        elif tab_idx == 9:
            # Extrapolation
            self.extrap_comments_messages()

        # elif tab_idx == 10:
        #     # Edges
        #     self.edges_comments_messages()


    def config_gui(self):

        self.tab_all.setCurrentIndex(0)
        # After data is loaded enable GUI and buttons on toolbar
        self.tab_all.setEnabled(True)
        self.actionSave.setEnabled(True)
        self.actionComment.setEnabled(True)

        # Configure tabs and toolbar for the presence or absence of GPS data
        self.tab_all.setTabEnabled(6, False)
        self.actionGGA.setEnabled(False)
        self.actionVTG.setEnabled(False)
        self.actionON.setEnabled(False)
        self.actionOFF.setEnabled(False)
        for idx in self.checked_transects_idx:
            if self.meas.transects[idx].boat_vel.gga_vel is not None:
                self.tab_all.setTabEnabled(6, True)
                self.actionGGA.setEnabled(True)
                self.actionVTG.setEnabled(True)
                self.actionON.setEnabled(True)
                self.actionOFF.setEnabled(True)
                break

        # Configure tabs for the presence or absence of a compass
        if np.any(self.checked_transects_idx):
            heading = np.unique(self.meas.transects[self.checked_transects_idx[0]].sensors.heading_deg.internal.data)
        else:
            heading = np.array([0])

        if len(heading) > 1 and np.any(np.not_equal(heading, 0)):
            self.tab_all.setTabEnabled(2, True)
        else:
            self.tab_all.setTabEnabled(2, False)


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