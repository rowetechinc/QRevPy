from PyQt5 import QtWidgets, QtCore
import UI.wRIVRS_Demo as wRIVRS_Demo
import sys
from Classes.Measurement import Measurement
from UI.selectFile import OpenMeasurementDialog
from datetime import datetime


class RIVRS_Demo(QtWidgets.QMainWindow, wRIVRS_Demo.Ui_RIVRS_Demo):
    """This is a class used as a substitute of the real RIVRS QMainWindow class to demonstrate how to integrate
    RIVRS and QRev through the use of a controller class (RIVRS_Controller).

    """
    def __init__(self, parent=None, caller=None):
        """Initializes settings and connections.

        Parameters
        ----------
        caller: Object
            Identifies calling object.
        """
        super(RIVRS_Demo, self).__init__(parent)
        self.setupUi(self)

        # File used to store settings like the last folder opened
        self.settingsFile = 'QRev_Settings'

        # Create connections for buttons
        self.pb_load.clicked.connect(self.load_files)
        if caller is not None:
            # If the caller is identified then the grouping is complete and the button to open QRev is connected
            # to the caller's(RIVRS_Controller) Show_QRev function
            self.pb_qrev.clicked.connect(caller.Show_QRev)


    def load_files(self):
        """Opens a file open dialog to allow the user to select the measurement file(s) for processing.
        The measurement is processed using the automatic settings in QRev."""

        # Disable QRev button until the groupings list is created
        self.pb_qrev.setEnabled(False)

        # Open file selection dialog
        select = OpenMeasurementDialog(self)
        select.exec_()

        # Process selected measurement based on manufacturer
        if select.type == 'SonTek':
            # Create measurement object
            self.meas = Measurement(in_file=select.fullName, source='SonTek', proc_type='QRev')

        elif select.type == 'TRDI':
            # Create measurement object
            self.meas = Measurement(in_file=select.fullName[0], source='TRDI', proc_type='QRev',
                                    checked=select.checked)

        elif select.type == 'QRev':
            # NOTE: Loading QRev files is currently not supported in QRev
            self.meas = Measurement(in_file=select.fullName[0], source='QRev')

        # groupings would be determined by the user using the RIVRS interface. These are provided as a demo test.
        self.groupings = [[0,1], [2,3], [4,5]]

        # This is to show the processed transects are available to RIVRS. Demo purposes only.
        self.raw_data_table()

        # Enable QRev button
        self.pb_qrev.setEnabled(True)

    def raw_data_table(self):
        """Creates a table to demonstrate the results of the initial processing of the measurement transects
        prior to grouping.
        """

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
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.utcfromtimestamp(
                self.meas.transects[transect_id].date_time.start_serial_time), '%H:%M:%S')))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect start edge
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(self.meas.transects[transect_id].start_edge[0]))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect end time
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.utcfromtimestamp(
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

    def processed_transect_table(self, data):
        """Creates a table to demonstrate the results of the initial processing of the measurement transects
        prior to grouping.
        """

        # Setup table
        tbl = self.table_original

        # Add transect data
        for row, transect in enumerate(data):
            col = 0
            # File/transect name
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(transect['transect_file']))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect start time
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.utcfromtimestamp(
                transect['start_serial_time']), '%H:%M:%S')))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect start edge
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(''))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect end time
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.utcfromtimestamp(
                transect['end_serial_time']), '%H:%M:%S')))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect duration
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:5.1f}'.format(transect['duration'])))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect total discharge
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.2f}'.format(transect['processed_discharge'])))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect top discharge
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(''))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect middle discharge
            col += 1
            tbl.setItem(row, col,
                        QtWidgets.QTableWidgetItem(''))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect bottom discharge
            col += 1
            tbl.setItem(row, col,
                        QtWidgets.QTableWidgetItem(''))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect left discharge
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(''))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect right discharge
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(''))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()

    def processed_data_table(self, data):
        """Creates a table to demonstrate the grouped and processed data passed back to QRev
        """

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
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.utcfromtimestamp(
                data[row]['start_serial_time']), '%H:%M:%S')))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect end time
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.utcfromtimestamp(
                data[row]['end_serial_time']), '%H:%M:%S')))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

            # Transect total discharge
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.2f}'.format(data[row]['processed_discharge'])))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = RIVRS_Demo()
    window.show()
    app.exec_()