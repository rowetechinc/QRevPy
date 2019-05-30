from PyQt5 import QtWidgets, QtCore, QtGui
# from Classes.stickysettings import StickySettings as SSet
from PyQt5.QtCore import pyqtSignal, QObject

import UI.QRev_gui as QRev_gui
import sys
import threading
from UI.selectFile import OpenMeasurementDialog, SaveMeasurementDialog
from Classes.Measurement import Measurement
from Classes.Python2Matlab import Python2Matlab
from Classes.Sensors import Sensors
import numpy as np
from UI.Qtmpl import Qtmpl
from MiscLibs.common_functions import units_conversion
from datetime import datetime
from UI.Comment import Comment
from UI.Transects2Use import Transects2Use
from UI.Options import Options
from UI.MagVar import MagVar
from UI.HOffset import HOffset
from UI.HSource import HSource
from contextlib import contextmanager
import time


class QRev(QtWidgets.QMainWindow, QRev_gui.Ui_MainWindow):
    handle_args_trigger = pyqtSignal()
    gui_initialized = False
    command_arg = ""

    def __init__(self, parent=None):
        super(QRev, self).__init__(parent)
        self.settingsFile = 'QRev_Settings'
        self.units = units_conversion(units_id='English')
        self.save_all = True
        # self.settings = SSet(self.settingsFile)
        self.setupUi(self)

        # self.actionOpen.triggered.connect(self.selectMeasurement)
        # self.actionSave.triggered.connect(self.saveMeasurement)
        self.actionOpen.triggered.connect(self.select_measurement)
        self.actionSave.triggered.connect(self.save_measurement)
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


# Toolbar functions
# =================
    def selectMeasurement(self):
        """Select and load measurement, triggered by actionOpen
        """
        # Initialize open measurement dialog
        self.select_measurement()
        self.actionOpen.triggered.connect(self.select_measurement)
        self.actionSave.triggered.connect(self.save_measurement)
        self.gui_initialized = True

    def select_measurement(self):
        self.select = OpenMeasurementDialog(self)
        self.select.exec_()

        # Tried this but this didn't work either
        # self.msg = Loading()
        # self.select.exec_()

        # This doesn't seem to be working properly
        with self.wait_cursor():
            # Load and process measurement based on measurement type
            if self.select.type == 'SonTek':
                # Show folder name in GUI header

                # Create measurement object
                self.meas = Measurement(in_file=self.select.fullName, source='SonTek', proc_type='QRev')

            elif self.select.type == 'TRDI':
                # Show mmt filename in GUI header

                # Create measurement object
                self.meas = Measurement(in_file=self.select.fullName[0], source='TRDI', proc_type='QRev', checked=self.select.checked)

                # self.msg.destroy()
            elif self.select.type == 'QRev':
                self.meas = Measurement(in_file=self.select.fullName, source='QRev')
            else:
                print('Cancel')

            self.checked_transects_idx = Measurement.checked_transects(self.meas)
            self.h_external_valid = Measurement.h_external_valid(self.meas)
            self.actionSave.setEnabled(True)
            self.actionComment.setEnabled(True)
            self.update_main()

    def saveMeasurement(self):
        """Save measurement, triggered by actionSave
        """

    def save_measurement(self):
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
            self.comments_tab()

    def selectTransects(self):
        self.transects_2_use = Transects2Use(self)
        transects_selected = self.transects_2_use.exec_()
        selected_transects = []
        if transects_selected:
            with self.wait_cursor():
                for row in range(self.transects_2_use.tableSelect.rowCount()):
                    if self.transects_2_use.tableSelect.item(row, 0).checkState() == QtCore.Qt.Checked:
                        selected_transects.append(row)

                self.checked_transects_idx = selected_transects
                Measurement.selected_transects_changed(self.meas, self.checked_transects_idx)
                self.update_main()

    def setRef2BT(self):
        """Changes the navigation reference to Bottom Track
        """
        with self.wait_cursor():
            settings = Measurement.current_settings(self.meas)
            settings['NavRef'] = 'BT'
            Measurement.apply_settings(self.meas, settings)
            self.update_main()

    def setRef2GGA(self):
        """Changes the navigation reference to GPS GGA
        """
        with self.wait_cursor():
            settings = Measurement.current_settings(self.meas)
            settings['NavRef'] = 'GGA'
            Measurement.apply_settings(self.meas, settings)
            self.update_main()

    def setRef2VTG(self):
        """Changes the navigation reference to GPS VTG
        """
        with self.wait_cursor():
            settings = Measurement.current_settings(self.meas)
            settings['NavRef'] = 'VTG'
            Measurement.apply_settings(self.meas, settings)
            self.update_main()

    def compTracksOn(self):
        with self.wait_cursor():
            settings = Measurement.current_settings(self.meas)
            settings['CompTracks'] = 'On'
            Measurement.apply_settings(self.meas, settings)
            self.update_main()

    def compTracksOff(self):
        with self.wait_cursor():
            settings = Measurement.current_settings(self.meas)
            settings['CompTracks'] = 'Off'
            Measurement.apply_settings(self.meas, settings)
            self.update_main()

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
            else:
                if self.units['ID'] == 'English':
                    self.units = units_conversion(units_id='SI')
                    self.update_main()

            if self.options.rb_All.isChecked():
                self.save_all = True
            else:
                self.save_all = False

            if self.options.cb_stylesheet.isChecked():
                self.save_stylesheet = True
            else:
                self.save_all = False

# Main tab
# ========
    def update_main(self):
        """Update Gui
        """
        self.checked_transects_idx = Measurement.checked_transects(self.meas)
        self.actionCheck.setEnabled(True)

        if len(self.checked_transects_idx) == len(self.meas.transects):
            self.actionCheck.setIcon(self.icon_allChecked)
        else:
            self.actionCheck.setIcon(self.icon_unChecked)

        # Set toolbar navigation indicator
        font_bold = QtGui.QFont()
        font_bold.setBold(True)
        font_bold.setPointSize(11)

        font_normal = QtGui.QFont()
        font_normal.setBold(False)
        font_normal.setPointSize(11)

        bt_selected = self.meas.transects[self.checked_transects_idx[0]].boat_vel.selected
        if bt_selected == 'bt_vel':
            self.actionBT.setFont(font_bold)
            self.actionGGA.setFont(font_normal)
            self.actionVTG.setFont(font_normal)
        elif bt_selected == 'gga_vel':
            self.actionBT.setFont(font_normal)
            self.actionGGA.setFont(font_bold)
            self.actionVTG.setFont(font_normal)
        elif bt_selected == 'vtg_vel':
            self.actionBT.setFont(font_normal)
            self.actionGGA.setFont(font_normal)
            self.actionVTG.setFont(font_bold)

        if self.meas.transects[self.checked_transects_idx[0]].boat_vel.composite == 'On':
            self.actionON.setFont(font_bold)
            self.actionOFF.setFont(font_normal)
        else:
            self.actionON.setFont(font_normal)
            self.actionOFF.setFont(font_bold)

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
        print('complete')

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
        # canvas_size = self.middle_canvas.size()
        # dpi = app.screens()[0].physicalDotsPerInch()

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

        # canvas_size = self.middle_canvas.size()
        # dpi = app.screens()[0].physicalDotsPerInch()

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

        # canvas_size = self.middle_canvas.size()
        # dpi = app.screens()[0].physicalDotsPerInch()

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
        # tbl.cellClicked.connect(self.select_transect)

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
            # checked = QtWidgets.QTableWidgetItem()
            # if self.meas.transects[row].checked:
            #     checked.setCheckState(QtCore.Qt.Checked)
            # else:
            #     checked.setCheckState(QtCore.Qt.Unchecked)
            #
            # tbl.setItem(row + 1, col, checked)
            # col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].file_name[:-4]))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.fromtimestamp(
                self.meas.transects[transect_id].date_time.start_serial_time), '%H:%M:%S')))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].start_edge[0]))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.fromtimestamp(
                self.meas.transects[transect_id].date_time.end_serial_time), '%H:%M:%S')))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:5.1f}'.format(
                self.meas.transects[transect_id].date_time.transect_duration_sec)))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:8.2f}'.format(self.meas.discharge[transect_id].total
                                                                                  * self.units['Q'])))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[transect_id].top
                                                                                  * self.units['Q'])))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[transect_id].middle
                                                                                  * self.units['Q'])))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[transect_id].bottom
                                                                                  * self.units['Q'])))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[transect_id].left
                                                                                  * self.units['Q'])))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[transect_id].right
                                                                                  * self.units['Q'])))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)

        # Add measurement summaries
        col = 0
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(self.tr('Measurement')))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(tbl.item(1, col).text()))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(''))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(tbl.item(nrows, col).text()))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:5.1f}'.format(Measurement.measurement_duration(self.meas))))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        discharge = Measurement.mean_discharges(self.meas)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:8.2f}'.format(discharge['total_mean'] * self.units['Q'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(discharge['top_mean'] * self.units['Q'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(discharge['mid_mean'] * self.units['Q'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(discharge['bot_mean'] * self.units['Q'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(discharge['left_mean'] * self.units['Q'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(discharge['right_mean'] * self.units['Q'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        for col in range(ncols):
            tbl.item(0, col).setFont(self.font_bold)

        tbl.item(1, 0).setFont(self.font_bold)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def main_details_table(self):
        # Setup table
        tbl = self.main_table_details
        summary_header = [self.tr('Transect'),
                          self.tr('Width' + ' ' + self.units['label_L']),
                          self.tr('Area' + ' ' + self.units['label_A']),
                          self.tr('Avg Boat Speed' + ' ' + self.units['label_V']),
                          self.tr('Course Made Good' + ' (deg)'),
                          self.tr('Q/A' + ' ' + self.units['label_V']),
                          self.tr('Avg Water Direction' + ' (deg)')]
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

            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].file_name[:-4]))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            item = '{:10.2f}'.format(trans_prop['width'][transect_id])
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            item = '{:10.2f}'.format(trans_prop['area'][transect_id])
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            item = '{:6.2f}'.format(trans_prop['avg_boat_speed'][transect_id])
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            item = '{:6.2f}'.format(trans_prop['avg_boat_course'][transect_id])
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            item = '{:6.2f}'.format(trans_prop['avg_water_speed'][transect_id])
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            item = '{:6.2f}'.format(trans_prop['avg_water_dir'][transect_id])
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)


        # Add measurement summaries
        n_transects = len(self.meas.transects)
        col = 0
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(self.tr('Average')))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)

        col += 1
        item = '{:10.2f}'.format(trans_prop['width'][n_transects])
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        item = '{:10.2f}'.format(trans_prop['area'][n_transects])
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        item = '{:6.2f}'.format(trans_prop['avg_boat_speed'][n_transects])
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1

        col += 1
        item = '{:6.2f}'.format(trans_prop['avg_water_speed'][n_transects])
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        item = '{:6.2f}'.format(trans_prop['avg_water_dir'][n_transects])
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem(item))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)


        for col in range(ncols):
            if col != 4:
                tbl.item(0, col).setFont(self.font_bold)

        tbl.item(1, 0).setFont(self.font_bold)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def main_premeasurement_table(self):

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
        if not self.meas.system_test:
            tbl.setItem(0, 1, QtWidgets.QTableWidgetItem(self.tr('No')))
        else:
            tbl.setItem(0, 1, QtWidgets.QTableWidgetItem(self.tr('Yes')))
        tbl.item(0, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.setItem(0, 2, QtWidgets.QTableWidgetItem(self.tr('ADCP Test Fails: ')))
        tbl.item(0, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(0, 2).setFont(self.font_bold)
        num_tests_with_failure = 0
        for test in self.meas.system_test:
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

        # Temperature
        tbl.setItem(3, 0, QtWidgets.QTableWidgetItem(self.tr('External Temperature (C): ')))
        tbl.item(3, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(3, 0).setFont(self.font_bold)
        if type(self.meas.ext_temp_chk['user']) != float:
            tbl.setItem(3, 1, QtWidgets.QTableWidgetItem(self.tr('N/A')))
        else:
            tbl.setItem(3, 1, QtWidgets.QTableWidgetItem('{:4.1f}'.format(self.meas.ext_temp_chk['user'])))
        tbl.item(3, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.setItem(3, 2, QtWidgets.QTableWidgetItem(self.tr('ADCP Temperature (C): ')))
        tbl.item(3, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(3, 2).setFont(self.font_bold)
        if type(self.meas.ext_temp_chk['adcp']) != float:
            avg_temp = Sensors.avg_temperature(self.meas.transects)
            tbl.setItem(3, 3, QtWidgets.QTableWidgetItem('{:4.1f}'.format(avg_temp)))
        else:
            tbl.setItem(3, 3, QtWidgets.QTableWidgetItem('{:4.1f}'.format(self.meas.ext_temp_chk['adcp'])))
        tbl.item(3, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        # Mag var and heading offset
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
        self.meas.station_name = self.ed_site_name.text()

    def update_site_number(self):
        self.meas.station_number = self.ed_site_name.text()

    def main_settings_table(self):
        # Setup table
        tbl = self.table_settings
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(nrows + 3)
        tbl.setColumnCount(14)
        tbl.horizontalHeader().hide()
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        tbl.cellClicked.connect(self.settings_table_row_adjust)
        # Build column labels
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

            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].file_name[:-4]))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1

            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(
                '{:5.1f}'.format(self.meas.transects[transect_id].edges.left.distance_m * self.units['L'])))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1

            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(
                '{:5.1f}'.format(self.meas.transects[transect_id].edges.right.distance_m * self.units['L'])))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1

            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(
                self.meas.transects[transect_id].edges.left.type[0:3]))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1

            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(
                self.meas.transects[transect_id].edges.right.type[0:3]))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1

            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(
                '{:5.2f}'.format(self.meas.transects[transect_id].depths.bt_depths.draft_use_m * self.units['L'])))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1

            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(
                '{:4.2f}'.format(self.meas.transects[transect_id].w_vel.excluded_dist_m * self.units['L'])))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)
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
            col += 1

            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].depths.composite))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)
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
            col += 1

            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].boat_vel.composite))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1

            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].extrap.top_method))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1

            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].extrap.bot_method))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1

            tbl.setItem(row + 3, col, QtWidgets.QTableWidgetItem(
                '{:5.4f}'.format(self.meas.transects[transect_id].extrap.exponent)))
            tbl.item(row + 3, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1

            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

            tbl.item(3, 0).setFont(self.font_bold)

    def settings_table_row_adjust(self, row, col):
        row = row - 2
        self.select_transect(row, col)

    def main_adcp_table(self):

        # Setup table
        tbl = self.table_adcp
        nrows = len(self.checked_transects_idx)
        tbl.setRowCount(4)
        tbl.setColumnCount(4)
        tbl.horizontalHeader().hide()
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # ADCP
        tbl.setItem(0, 0, QtWidgets.QTableWidgetItem(self.tr('Serial Number: ')))
        tbl.item(0, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(0, 0).setFont(self.font_bold)
        tbl.setItem(0, 1, QtWidgets.QTableWidgetItem(
            self.meas.transects[self.checked_transects_idx[0]].adcp.serial_num))
        tbl.item(0, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.setItem(0, 2, QtWidgets.QTableWidgetItem(self.tr('Manufacturer: ')))
        tbl.item(0, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(0, 2).setFont(self.font_bold)
        tbl.setItem(0, 3, QtWidgets.QTableWidgetItem(
            self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer))
        tbl.item(0, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.setItem(1, 0, QtWidgets.QTableWidgetItem(self.tr('Model: ')))
        tbl.item(1, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(1, 0).setFont(self.font_bold)
        tbl.setItem(1, 1, QtWidgets.QTableWidgetItem(self.meas.transects[self.checked_transects_idx[0]].adcp.model))
        tbl.item(1, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.setItem(1, 2, QtWidgets.QTableWidgetItem(self.tr('Firmware: ')))
        tbl.item(1, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(1, 2).setFont(self.font_bold)
        if type(self.meas.transects[self.checked_transects_idx[0]].adcp.firmware) == str:
            firmware = self.meas.transects[self.checked_transects_idx[0]].adcp.firmware
        else:
            firmware = str(self.meas.transects[self.checked_transects_idx[0]].adcp.firmware)
        tbl.setItem(1, 3, QtWidgets.QTableWidgetItem(firmware))
        tbl.item(1, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.setItem(2, 0, QtWidgets.QTableWidgetItem(self.tr('Frequency (kHz): ')))
        tbl.item(2, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(2, 0).setFont(self.font_bold)
        tbl.setItem(2, 1, QtWidgets.QTableWidgetItem(
            '{:4.0f}'.format(self.meas.transects[self.checked_transects_idx[0]].adcp.frequency_khz)))
        tbl.item(2, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.setItem(2, 2, QtWidgets.QTableWidgetItem(self.tr('Depth Cell Size (cm): ')))
        tbl.item(2, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(2, 2).setFont(self.font_bold)
        cell_sizes = []
        for n in range(len(self.checked_transects_idx)):
            transect = self.meas.transects[self.checked_transects_idx[n]]
            cell_sizes.append(np.unique(transect.depths.bt_depths.depth_cell_size_m))
        max_cell_size = np.nanmax(cell_sizes) * 100
        min_cell_size = np.nanmin(cell_sizes) * 100
        if max_cell_size - min_cell_size < 1:
            size = '{:3.0f}'.format(max_cell_size)
        else:
            size = '{:3.0f} - {:3.0f}'.format(min_cell_size, max_cell_size)
        tbl.setItem(2, 3, QtWidgets.QTableWidgetItem(size))
        tbl.item(2, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.setItem(3, 0, QtWidgets.QTableWidgetItem(self.tr('Water Mode: ')))
        tbl.item(3, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(3, 0).setFont(self.font_bold)
        tbl.setItem(3, 1, QtWidgets.QTableWidgetItem(
            '{:2.0f}'.format(self.meas.transects[self.checked_transects_idx[0]].w_vel.water_mode)))
        tbl.item(3, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.setItem(3, 2, QtWidgets.QTableWidgetItem(self.tr('Bottom Mode: ')))
        tbl.item(3, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(3, 2).setFont(self.font_bold)
        tbl.setItem(3, 3, QtWidgets.QTableWidgetItem(
            '{:2.0f}'.format(self.meas.transects[self.checked_transects_idx[0]].boat_vel.bt_vel.bottom_mode)))
        tbl.item(3, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def custom_header(self, tbl, row, col, row_span, col_span, text):
        tbl.setItem(row, col, QtWidgets.QTableWidgetItem(text))
        tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, col).setFont(self.font_bold)
        tbl.setSpan(row, col, row_span, col_span)
        tbl.setWordWrap(True)

    # System test tab
    # ===============
    def system_tab(self, idx_systest=0):

        # Setup table
        tbl = self.table_systest

        nrows = len(self.meas.system_test)
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
            for row, test in enumerate(self.meas.system_test):
                col = 0
                tbl.setItem(row, col, QtWidgets.QTableWidgetItem(test.time_stamp))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                col += 1

                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:2.0f}'.format(test.result['n_tests'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                col += 1

                tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:2.0f}'.format(test.result['n_failed'])))
                tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
                col += 1

                if len(self.meas.qa.system_tst['messages']) > 0:
                    if self.meas.transects[self.checked_transects_idx[0]].adcp.manufacturer == 'TRDI':
                        if any("PT3" in item for item in self.meas.qa.system_test['messages']):
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

                tbl.item(idx_systest, 0).setFont(self.font_bold)
                self.display_systest.textCursor().insertText(self.meas.system_test[idx_systest].data)

                tbl.resizeColumnsToContents()
                tbl.resizeRowsToContents()

        # Comments
        self.display_systest_comments.clear()
        if hasattr(self, 'meas'):
            self.display_systest_comments.moveCursor(QtGui.QTextCursor.Start)
            for comment in self.meas.comments:
                # Display each comment on a new line
                self.display_systest_comments.textCursor().insertText(comment)
                self.display_systest_comments.moveCursor(QtGui.QTextCursor.End)
                self.display_systest_comments.textCursor().insertBlock()

            self.display_systest_comments.moveCursor(QtGui.QTextCursor.Start)
            for message in self.meas.qa.system_tst['messages']:
                # Display each comment on a new line
                self.display_systest_messages.textCursor().insertText(message)
                self.display_systest_messages.moveCursor(QtGui.QTextCursor.End)
                self.display_systest_messages.textCursor().insertBlock()

    def select_systest(self, row, column):
        tbl = self.table_systest
        if column == 0:
            with self.wait_cursor():
                # Set all files to normal font
                nrows = len(self.meas.system_test)
                for nrow in range(1, nrows):
                    self.self.table_systest(nrow, 0).setFont(self.font_normal)

                # Set selected file to bold font
                self.table_systest.item(row, 0).setFont(self.font_bold)

                # Update contour and shiptrack plot
                self.system_tab(idx_systest=row)

    # Compass tab
    # ===========
    def compass_tab(self):


        # Setup table
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
        self.update_compass_tab(tbl=tbl, old_discharge=self.meas.discharge,
                                new_discharge=self.meas.discharge)

    def update_compass_tab(self, tbl, old_discharge, new_discharge):

        for row in range(tbl.rowCount()):
            transect_id = self.checked_transects_idx[row]

            col = 0
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].file_name[:-4]))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(
                self.meas.transects[transect_id].sensors.heading_deg.internal.mag_var_deg)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(
                self.meas.transects[transect_id].sensors.heading_deg.internal.align_correction_deg)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(
                self.meas.transects[transect_id].sensors.heading_deg.selected))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            col += 1
            pitch = getattr(self.meas.transects[transect_id].sensors.pitch_deg,
                            self.meas.transects[transect_id].sensors.pitch_deg.selected)
            item = np.nanmean(pitch.data)
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(item)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            col += 1
            item = np.nanstd(pitch.data, ddof=1)
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(item)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            col += 1
            roll = getattr(self.meas.transects[transect_id].sensors.roll_deg,
                           self.meas.transects[transect_id].sensors.roll_deg.selected)
            item = np.nanmean(roll.data)
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(item)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            col += 1
            item = np.nanstd(roll.data, ddof=1)
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(item)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(old_discharge[transect_id].total)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.1f}'.format(new_discharge[transect_id].total)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            col += 1
            per_change = ((new_discharge[transect_id].total - old_discharge[transect_id].total)
                          / old_discharge[transect_id].total) * 100
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:3.1f}'.format(per_change)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()

    def compass_table_clicked(self, row, column):
        tbl = self.table_compass_pr
        with self.wait_cursor():
            # Magnetic variation
            if column == 1:
                # Intialize dialog
                magvar_dialog = MagVar(self)
                magvar_entered = magvar_dialog.exec_()
                # Data entered.
                if magvar_entered:
                    old_discharge = self.meas.discharge
                    magvar = float(magvar_dialog.ed_magvar.text())
                    if magvar_dialog.rb_all.isChecked():
                        self.meas.change_magvar(magvar=magvar)
                    else:
                        self.meas.change_magvar( magvar=magvar, transect_idx=self.transects_2_use[row])
                    self.update_compass_tab(tbl=tbl, old_discharge=old_discharge, new_discharge=self.meas.discharge)

            # Heading Offset
            elif column == 2:
                if self.h_external_valid:
                    # Intialize dialog
                    h_offset_dialog = HOffset(self)
                    h_offset_entered = h_offset_dialog.exec_()
                    # If data entered.
                    if h_offset_entered:
                        old_discharge = self.meas.discharge
                        h_offset = float(h_offset_dialog.ed_hoffset.text())
                        if h_offset_dialog.rb_all.isChecked():
                            self.meas.change_h_offset(h_offset=h_offset)
                        else:
                            self.meas.change_h_offset(h_offset=h_offset, transect_idx=self.transects_2_use[row])

                        self.update_compass_tab(tbl=tbl, old_discharge=old_discharge, new_discharge=self.meas.discharge)
            # Heading Source
            elif column == 3:
                if self.h_external_valid:
                    # Intialize dialog
                    h_source_dialog = HSource(self)
                    h_source_entered = h_source_dialog.exec_()
                    # If data entered.
                    if h_source_entered:
                        old_discharge = self.meas.discharge
                        if h_source_dialog.rb_internal:
                            h_source = 'internal'
                        else:
                            h_source = 'external'
                        if h_source_dialog.rb_all.isChecked():
                            self.meas.change_h_source(h_source=h_source)
                        else:
                            self.meas.change_h_source(h_source=h_source, transect_idx=self.transects_2_use[row])

                        self.update_compass_tab(tbl=tbl, old_discharge=old_discharge, new_discharge=self.meas.discharge)

# Split fuctions
# ==============
    def split_initialization(self, pairings, data):
        # Setting to allow processing to split measurement into multiple measurements
        if pairings is not None:
            self.save_all = False
            self.actionSave.triggered.connect(self.split_save)
            self.actionOpen.setEnabled(False)
            self.actionCheck.setEnabled(False)
            self.meas = data
            self.pairings = pairings
            self.pair_idx = 0
            self.split_processing(pairings[self.pair_idx])

    def split_processing(self, group):

        Measurement.selected_transects_changed(self.meas, group)
        self.update_main()

    def split_save(self):
        # Create default file name
        save_file = SaveMeasurementDialog()

        # Save data in Matlab format
        if self.save_all:
            Python2Matlab.save_matlab_file(self.meas, save_file.full_Name)
        else:
            Python2Matlab.save_matlab_file(self.meas, save_file.full_Name, checked=self.pairings[self.pair_idx])

        q = {'group': self.pairings[self.pair_idx],
             'start_serial_time': self.meas.transects[self.pairings[self.pair_idx][0]].date_time.start_serial_time,
             'end_serial_time': self.meas.transects[self.pairings[self.pair_idx][-1]].date_time.end_serial_time,
             'processed_discharge': self.meas.discharge[-1].total}
        self.processed_data.append(q)
        self.pair_idx += 1

        if self.pair_idx > len(self.pairings) - 1:
            self.accept()

# Support functions
# =================
    @contextmanager
    def wait_cursor(self):
        try:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            yield
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    # def update_meas(self, meas):
    #
    #     self.meas = meas
    #     self.main_summary_table()
    #     self.uncertainty_table()
    #     self.qa_table()
    #     self.contour_shiptrack()

    def tab_manager(self, tab_idx):
        if tab_idx == 0:
            self.update_main()
        elif tab_idx == 1:
            self.system_tab()
        elif tab_idx == 2:
            self.compass_tab()

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
elif __name__ == 'UI.MeasSplitter':
    app = QtWidgets.QApplication(sys.argv)
    window = QRev()
    window.show()
    app.exec_()