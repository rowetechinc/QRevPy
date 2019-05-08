import os
from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime
import scipy.io as sio
# from Classes.stickysettings import StickySettings as SSet
import UI.QRev_gui as QRev_gui
import sys
from UI.selectFile import OpenMeasurementDialog, SaveMeasurementDialog
from Classes.Measurement import Measurement
# from Classes.ComputeExtrap import ComputeExtrap
# from Classes.QComp import QComp
from Classes.Python2Matlab import Python2Matlab
# from Classes.CommonDataComp import CommonDataComp
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from UI.Qtmpl import Qtmpl
from MiscLibs.common_functions import units_conversion
from datetime import datetime
from UI.Comment import Comment
from UI.Transects2Use import Transects2Use
from UI.Options import Options
from UI.Loading import Loading
from contextlib import contextmanager
import time



class QRev(QtWidgets.QMainWindow, QRev_gui.Ui_MainWindow):


    def __init__(self, parent=None):
        super(QRev, self).__init__(parent)
        self.settingsFile = 'QRev_Settings'
        self.units = units_conversion(units_id='English')
        self.save_all = True
        # self.settings = SSet(self.settingsFile)
        self.setupUi(self)
        self.actionOpen.triggered.connect(self.selectMeasurement)
        self.actionSave.triggered.connect(self.saveMeasurement)
        self.actionComment.triggered.connect(self.addComment)
        self.actionCheck.triggered.connect(self.selectTransects)
        self.actionBT.triggered.connect(self.setRef2BT)
        self.actionGGA.triggered.connect(self.setRef2GGA)
        self.actionVTG.triggered.connect(self.setRef2VTG)
        self.actionOFF.triggered.connect(self.compTracksOff)
        self.actionON.triggered.connect(self.compTracksOn)
        self.actionOptions.triggered.connect(self.qrev_options)

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
        self.icon_unChecked.addPixmap(QtGui.QPixmap(":/images/24x24/Red mark.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

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

    def selectMeasurement(self):
        """Select and load measurement, triggered by actionOpen
        """
        # Initialize open measurement dialog
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

            self.actionSave.setEnabled(True)
            self.actionComment.setEnabled(True)
            self.update_main()

    def update_main(self):
        """Update Gui
        """

        self.actionCheck.setEnabled(True)
        self.checked_transects_idx = Measurement.checked_transects(self.meas)
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
        print('complete')

    def saveMeasurement(self):
        """Save measurement, triggered by actionSave
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
            tbl.setItem(row, 2, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.extrapolation_95_user)))

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
                # Set selected file to bold font
                self.main_table_summary.item(row, 0).setFont(self.font_bold)
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

    @contextmanager
    def wait_cursor(self):
        try:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            yield
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

app = QtWidgets.QApplication(sys.argv)
window = QRev()
window.show()
app.exec_()