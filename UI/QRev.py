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
from UI.MainMiddleMpl import MainMiddleMpl
from MiscLibs.common_functions import units_conversion


class QRev(QtWidgets.QMainWindow, QRev_gui.Ui_MainWindow):


    def __init__(self, parent=None):
        super(QRev, self).__init__(parent)
        self.settingsFile = 'QRev_Settings'
        # self.settings = SSet(self.settingsFile)
        self.setupUi(self)
        self.actionOpen.triggered.connect(self.selectMeasurement)
        self.actionSave.triggered.connect(self.saveMeasurement)

    def selectMeasurement(self):
        self.select = OpenMeasurementDialog(self)
        self.select.exec_()
        if self.select.type == 'SonTek':
            # Show folder name in GUI header

            # Create measurement object
            self.meas = Measurement(in_file=self.select.fullName, source='SonTek', proc_type='QRev')

        elif self.select.type == 'TRDI':
            # Show mmt filename in GUI header

            # Create measurement object
            self.meas = Measurement(in_file=self.select.fullName[0], source='TRDI', proc_type='QRev', checked=self.select.checked)

        elif self.select.type == 'QRev':
            self.meas = Measurement(in_file=self.select.fullName, source='QRev')
        else:
            print('Cancel')

        self.main_summary_table()
        self.uncertainty_table()
        self.qa_table()
        self.shiptrack()
        print('complete')

    def saveMeasurement(self):
        # Create default file name
        save_file = SaveMeasurementDialog()
        Python2Matlab.save_matlab_file(self.meas, save_file.full_Name)

    def openFile(self):
        # Get the current folder setting. However, if the folder has not been previously defined create the Folder key
        # and set the value the current folder.
        try:
            folder = self.settings.get('Folder')
        except KeyError:
            self.settings.new('Folder',os.getcwd())
            folder = self.settings.get('Folder')
        # Allow the user to choose the file to open.
        fileName = QtWidgets.QFileDialog.getOpenFileName(self,self.tr('Open File'),folder,self.tr('Any File (*.mat)'))[0]
        # Update the folder setting
        pathName = os.path.split(fileName)[0]
        self.settings.set('Folder',pathName)
        # Read Matlab file
        mat_contents = sio.loadmat(fileName, struct_as_record=False, squeeze_me=True)
        # For QRev File
        meas_struct = mat_contents['meas_struct']
        QRev_version = mat_contents['version']
        print('Hello World')
        mat_struct = mat_contents['meas_struct']

    def main_summary_table(self):
        # Setup table
        tbl = self.main_table_summary
        main_summary_header = [self.tr('Transect'), self.tr('Start'), self.tr('Bank'), self.tr('End'),
                               self.tr('Duration'), self.tr('Total Q'), self.tr('Top Q'), self.tr('Meas Q'),
                               self.tr('Bottom Q'), self.tr('Left Q'), self.tr('Right Q')]
        ncols = len(main_summary_header)
        nrows = len(self.meas.transects)
        tbl.setRowCount(nrows + 1)
        tbl.setColumnCount(ncols)
        font_bold = QtGui.QFont()
        font_bold.setBold(True)
        tbl.setHorizontalHeaderLabels(main_summary_header)
        tbl.horizontalHeader().setFont(font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Add transect data
        for row in range(nrows):
            col = 0
            # checked = QtWidgets.QTableWidgetItem()
            # if self.meas.transects[row].checked:
            #     checked.setCheckState(QtCore.Qt.Checked)
            # else:
            #     checked.setCheckState(QtCore.Qt.Unchecked)
            #
            # tbl.setItem(row + 1, col, checked)
            # col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(self.meas.transects[row].file_name[:-4]))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.fromtimestamp(
                self.meas.transects[row].date_time.start_serial_time), '%H:%M:%S')))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(self.meas.transects[row].start_edge[0]))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.fromtimestamp(
                self.meas.transects[row].date_time.end_serial_time), '%H:%M:%S')))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:5.1f}'.format(
                self.meas.transects[row].date_time.transect_duration_sec)))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:8.2f}'.format(self.meas.discharge[row].total)))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[row].top)))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[row].middle)))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[row].bottom)))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[row].left)))
            tbl.item(row + 1, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row + 1, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[row].right)))
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
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:8.2f}'.format(discharge['total_mean'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(discharge['top_mean'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(discharge['mid_mean'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(discharge['bot_mean'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(discharge['left_mean'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        col += 1
        tbl.setItem(0, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(discharge['right_mean'])))
        tbl.item(0, col).setFlags(QtCore.Qt.ItemIsEnabled)
        for col in range(ncols):
            tbl.item(0, col).setFont(font_bold)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def uncertainty_table(self):
        tbl = self.table_uncertainty
        col_header = [self.tr('Uncertainty'), self.tr('Auto'), self.tr('  User  ')]
        ncols = len(col_header)
        nrows = 7
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        font_bold = QtGui.QFont()
        font_bold.setBold(True)
        tbl.setHorizontalHeaderLabels(col_header)
        tbl.horizontalHeader().setFont(font_bold)
        tbl.verticalHeader().hide()
        # tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

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
        font_bold = QtGui.QFont()
        font_bold.setBold(True)
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr('Estimated 95%')))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 0).setFont(font_bold)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.total_95)))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 1).setFont(font_bold)
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem('{:8.1f}'.format(self.meas.uncertainty.total_95_user)))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 2).setFont(font_bold)
        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

        tbl.itemChanged.connect(self.recompute_uncertainty)

    def recompute_uncertainty(self):
        new_value = self.table_uncertainty.selectedItems()[0].text()
        if new_value == '':
            new_value = None
        else:
            new_value = float(new_value)
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

        self.meas.uncertainty.estimate_total_uncertainty()
        if new_value is not None:
            self.table_uncertainty.item(row_index, 2).setText('{:8.1f}'.format(new_value))
        self.table_uncertainty.item(6, 2).setText('{:8.1f}'.format(self.meas.uncertainty.total_95_user))

    def qa_table(self):
        tbl = self.table_qa
        header = ['', self.tr('COV %'), '', self.tr('% Q')]
        ncols = len(header)
        nrows = 3
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        font_bold = QtGui.QFont()
        font_bold.setBold(True)
        tbl.setHorizontalHeaderLabels(header)
        tbl.horizontalHeader().setFont(font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Compute measurement properties
        trans_prop = self.meas.compute_measurement_properties(self.meas)
        discharge = self.meas.mean_discharges(self.meas)

        row = 0
        # Discharge COV
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr('Q:')))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 0).setFont(font_bold)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('{:5.2f}'.format(self.meas.uncertainty.cov)))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Left and right edge % Q
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(self.tr('L/R Edge:')))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 2).setFont(font_bold)
        left = (discharge['left_mean'] / discharge['total_mean']) * 100
        right = (discharge['right_mean'] / discharge['total_mean']) * 100
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem('{:5.2f} / {:5.2f}'.format(left, right)))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        row = row + 1
        # Width COV
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr('Width:')))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 0).setFont(font_bold)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('{:5.2f}'.format(trans_prop['width_cov'][-1])))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Invalid cells
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(self.tr('Invalid Cells:')))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 2).setFont(font_bold)
        value = (discharge['int_cells_mean'] / discharge['total_mean']) * 100
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem('{:5.2f}'.format(value)))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        row = row + 1
        # Area COV
        tbl.setItem(row, 0, QtWidgets.QTableWidgetItem(self.tr('Area:')))
        tbl.item(row, 0).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 0).setFont(font_bold)
        tbl.setItem(row, 1, QtWidgets.QTableWidgetItem('{:5.2f}'.format(trans_prop['area_cov'][-1])))
        tbl.item(row, 1).setFlags(QtCore.Qt.ItemIsEnabled)

        # Invalid ensembles
        tbl.setItem(row, 2, QtWidgets.QTableWidgetItem(self.tr('Invalid Ens:')))
        tbl.item(row, 2).setFlags(QtCore.Qt.ItemIsEnabled)
        tbl.item(row, 2).setFont(font_bold)
        value = (discharge['int_ensembles_mean'] / discharge['total_mean']) * 100
        tbl.setItem(row, 3, QtWidgets.QTableWidgetItem('{:5.2f}'.format(value)))
        tbl.item(row, 3).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

# class ShipTrack(FigureCanvas):
#
#     def __init__(self, meas, parent=None, width=5, height=4, dpi=100):
#         fig = Figure(figsize=(width, height), dpi=dpi)
#         self.axes = fig.add_subplot(111)
#
#         FigureCanvas._init_(self.fig)
#         self.setParent(parent)
#
#         FigureCanvas.setSizePolicy(self,
#                                    QSizePolicy.Expanding,
#                                    QSizePolicy.Expanding)
#         FigureCanvas.updateGeometry(self)
#         self.shiptrack(meas)
#     def shiptrack2(self):
#
#         # Get measurement data
#         meas = self.meas
#
#         # Initialize figure
#         #st_fig, ax1 = plt.subplots()
#         # ax1 = self.figure.add_subplot(111)
#         dpi = app.screens()[0].physicalDotsPerInch()
#         height = self.main_shiptrack.height() * 0.8 / dpi
#         width = self.main_shiptrack.width() * 0.8 / dpi
#         st_fig = Figure()
#         ax1 = st_fig.add_subplot(111)
#         _ = ax1.axis('equal')
#         ax1.grid()
#
#         units = units_conversion(units_id='SI')
#
#         # Plot all available shiptracks
#         ship_data_bt = meas.transects[0].boat_vel.compute_boat_track(meas.transects[0], ref='bt_vel')
#         ax1.plot(ship_data_bt['track_x_m'] * units['L'], ship_data_bt['track_y_m'] * units['L'], color='r',
#                  label='BT')
#         ship_data = ship_data_bt
#
#         if meas.transects[0].boat_vel.vtg_vel is not None:
#             ship_data_vtg = meas.transects[0].boat_vel.compute_boat_track(meas.transects[0], ref='vtg_vel')
#             ax1.plot(ship_data_vtg['track_x_m'] * units['L'], ship_data_vtg['track_y_m'] * units['L'], color='g',
#                      label='VTG')
#             if meas.transects[0].boat_vel.selected == 'vtg_vel':
#                 ship_data = ship_data_vtg
#
#         if meas.transects[0].boat_vel.gga_vel is not None:
#             ship_data_gga = meas.transects[0].boat_vel.compute_boat_track(meas.transects[0], ref='gga_vel')
#             ax1.plot(ship_data_gga['track_x_m'] * units['L'], ship_data_gga['track_y_m'] * units['L'], color='b',
#                      label='GGA')
#             if meas.transects[0].boat_vel.selected == 'gga_vel':
#                 ship_data = ship_data_gga
#
#         ax1.set_xlabel('Distance East ')
#         ax1.set_ylabel('Distance North ')
#
#         # Compute mean water velocity for each ensemble
#         u = meas.transects[0].w_vel.u_processed_mps
#         v = meas.transects[0].w_vel.v_processed_mps
#         u_mean = np.nanmean(u, axis=0)
#         v_mean = np.nanmean(v, axis=0)
#
#         quiv_plt = ax1.quiver(ship_data['track_x_m'] * units['L'], ship_data['track_y_m'] * units['L'],
#                               u_mean * units['V'], v_mean * units['V'], units='dots', width=2, scale=.02)
#         # qk = ax1.quiverkey(quiv_plt, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
#         #                    coordinates='figure')
#
#
#         ax1.legend(loc='best')
#
#         scene = QtWidgets.QGraphicsScene(self)
#         canvas = FigureCanvas(st_fig)
#         canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
#         # canvas.setGeometry(0, 0, self.main_shiptrack.height() * 0.8, self.main_shiptrack.width() * 0.8)
#         canvas.draw()
#         scene.addWidget(canvas)
#         self.main_shiptrack.setScene(scene)
#
#     def shiptrack3(self):
#
#         # Get measurement data
#         meas = self.meas
#         ax1 = self.main_shiptrack.canvas.axes
#         ax1.clear()
#
#         _ = ax1.axis('equal')
#         ax1.grid()
#
#         units = units_conversion(units_id='SI')
#
#         # Plot all available shiptracks
#         ship_data_bt = meas.transects[0].boat_vel.compute_boat_track(meas.transects[0], ref='bt_vel')
#         ax1.plot(ship_data_bt['track_x_m'] * units['L'], ship_data_bt['track_y_m'] * units['L'], color='r',
#                  label='BT')
#         ship_data = ship_data_bt
#
#         if meas.transects[0].boat_vel.vtg_vel is not None:
#             ship_data_vtg = meas.transects[0].boat_vel.compute_boat_track(meas.transects[0], ref='vtg_vel')
#             ax1.plot(ship_data_vtg['track_x_m'] * units['L'], ship_data_vtg['track_y_m'] * units['L'], color='g',
#                      label='VTG')
#             if meas.transects[0].boat_vel.selected == 'vtg_vel':
#                 ship_data = ship_data_vtg
#
#         if meas.transects[0].boat_vel.gga_vel is not None:
#             ship_data_gga = meas.transects[0].boat_vel.compute_boat_track(meas.transects[0], ref='gga_vel')
#             ax1.plot(ship_data_gga['track_x_m'] * units['L'], ship_data_gga['track_y_m'] * units['L'], color='b',
#                      label='GGA')
#             if meas.transects[0].boat_vel.selected == 'gga_vel':
#                 ship_data = ship_data_gga
#
#         ax1.set_xlabel('Distance East ')
#         ax1.set_ylabel('Distance North ')
#         ax1.xaxis.label.set_fontsize(8)
#         ax1.yaxis.label.set_fontsize(8)
#         for label in (ax1.get_xticklabels() + ax1.get_yticklabels()):
#             label.set_fontsize(8)
#
#         # Compute mean water velocity for each ensemble
#         u = meas.transects[0].w_vel.u_processed_mps
#         v = meas.transects[0].w_vel.v_processed_mps
#         u_mean = np.nanmean(u, axis=0)
#         v_mean = np.nanmean(v, axis=0)
#
#         quiv_plt = ax1.quiver(ship_data['track_x_m'] * units['L'], ship_data['track_y_m'] * units['L'],
#                               u_mean * units['V'], v_mean * units['V'], units='dots', width=2, scale=.02)
#         # qk = ax1.quiverkey(quiv_plt, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E',
#         #                    coordinates='figure')
#
#         ax1.legend(loc='best')
#         self.main_shiptrack.canvas.draw()

    def shiptrack(self):
        l = QtWidgets.QVBoxLayout(self.main_shiptrack)
        st = MainMiddleMpl(self.main_shiptrack, width=4, height=4, dpi=60, data=self.meas)
        # dc = MyDynamicMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        l.addWidget(st)
        # l.addWidget(dc)

        self.main_shiptrack.setFocus()

app = QtWidgets.QApplication(sys.argv)
window = QRev()
window.show()
app.exec_()