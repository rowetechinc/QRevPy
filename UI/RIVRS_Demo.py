from PyQt5 import QtWidgets, QtCore
import UI.wRIVRS_Demo as wRIVRS_Demo
import sys
from Classes.Measurement import Measurement
from datetime import datetime


class RIVRS_Demo(QtWidgets.QMainWindow, wRIVRS_Demo.Ui_RIVRS_Demo):
    def __init__(self, parent=None, caller=None):
        """Initializes settings and connections.

        Parameters
        ----------
        parent
            Identifies parent GUI.
        """
        super(RIVRS_Demo, self).__init__(parent)
        self.setupUi(self)

        # Create connections for buttons
        self.pb_load.clicked.connect(self.load_files)
        if caller is not None:
            self.pb_qrev.clicked.connect(caller.Show_QRev)


    def load_files(self):
        """Finds all files in the folder and subfolder matching the criteria and saves them to a list."""

        # Disable save button until list is created
        self.pb_qrev.setEnabled(False)

        # Get top level folder from user
        fullName = QtWidgets.QFileDialog.getOpenFileNames(
            self, self.tr('Open File'))[0]

        source = 'TRDI'
        if source == 'SonTek':
            # Create measurement object
            self.meas = Measurement(in_file=fullName, source='SonTek', proc_type='QRev')

        elif source == 'TRDI':
            # Create measurement object
            self.meas = Measurement(in_file=fullName[0], source='TRDI', proc_type='QRev')

        elif source == 'QRev':
            self.meas = Measurement(in_file=fullName[0], source='QRev')

        self.pairings = [[0,1],[1,2], [0,2]]

        self.raw_data_table()

        # Enable save button
        self.pb_qrev.setEnabled(True)

    def raw_data_table(self):
        # Setup table
        tbl = self.table_original
        summary_header = [self.tr('Transect'), self.tr('Start'), self.tr('Bank'), self.tr('End'),
                          self.tr('Duration'), self.tr('Total Q'), self.tr('Top Q'), self.tr('Meas Q'),
                          self.tr('Bottom Q'), self.tr('Left Q'), self.tr('Right Q')]
        ncols = len(summary_header)
        nrows = len(self.meas.transects)
        tbl.setRowCount(nrows + 1)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(summary_header)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Add transect data
        for row in range(nrows):
            col = 0
            transect_id = row

            # File/transect name
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].file_name[:-4]))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect start time
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.fromtimestamp(
                self.meas.transects[transect_id].date_time.start_serial_time), '%H:%M:%S')))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect start edge
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].start_edge[0]))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect end time
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.fromtimestamp(
                self.meas.transects[transect_id].date_time.end_serial_time), '%H:%M:%S')))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect duration
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:5.1f}'.format(
                self.meas.transects[transect_id].date_time.transect_duration_sec)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect total discharge
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.2f}'.format(self.meas.discharge[transect_id].total)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect top discharge
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[transect_id].top)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect middle discharge
            col += 1
            tbl.setItem(row, col,
                        QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[transect_id].middle)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect bottom discharge
            col += 1
            tbl.setItem(row, col,
                        QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[transect_id].bottom)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect left discharge
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[transect_id].left)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect right discharge
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(self.meas.discharge[transect_id].right)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def processed_data_table(self, data):
        # Setup table
        tbl = self.table_processed
        summary_header = [self.tr('Transect Idx'), self.tr('Start'), self.tr('End'), self.tr('Total Q')]
        ncols = len(summary_header)
        nrows = len(data)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(summary_header)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Add transect data
        for row in range(nrows):
            col = 0


            # File/transect idx
            item = ', '.join(str(e) for e in data[row]['group'])
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(item))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect start time
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.fromtimestamp(
                data[row]['start_serial_time']), '%H:%M:%S')))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect end time
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.fromtimestamp(
                data[row]['end_serial_time']), '%H:%M:%S')))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect total discharge
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.2f}'.format(data[row]['processed_discharge'])))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = dsm_test_split()
    window.show()
    app.exec_()