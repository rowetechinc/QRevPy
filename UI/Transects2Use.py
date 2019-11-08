from PyQt5 import QtWidgets, QtCore
from UI import wTransects2Use
from datetime import datetime
from Classes.Measurement import Measurement


class Transects2Use(QtWidgets.QDialog, wTransects2Use.Ui_Transects2Use):
    """Dialog to allow users to to select and deselect transects to use in the discharge computation.

    Parameters
    ----------
    wTransects2Use.Ui_Transects2Use : QDialog
        Dialog window with options for users

    Attributes
    ----------

    """

    def __init__(self, parent=None):
        super(Transects2Use, self).__init__(parent)
        self.setupUi(self)
        # self.checked_transects_idx = parent.checked_transects_idx
        # self.meas = parent.meas

        self.summary_table(parent)

    def summary_table(self, parent):
        """Create and populate main summary table.
        """
        # Setup table
        tbl = self.tableSelect
        units = parent.units
        summary_header = [parent.tr('Select Transect'), parent.tr('Start'), parent.tr('Bank'),
                          parent.tr('End'), parent.tr('Duration'), parent.tr('Total Q'), parent.tr('Top Q'),
                          parent.tr('Meas Q'), parent.tr('Bottom Q'), parent.tr('Left Q'), parent.tr('Right Q')]
        ncols = len(summary_header)
        nrows = len(parent.meas.transects)
        tbl.setRowCount(nrows)
        tbl.setColumnCount(ncols)
        tbl.setHorizontalHeaderLabels(summary_header)
        tbl.horizontalHeader().setFont(parent.font_bold)
        tbl.verticalHeader().hide()
        tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        # tbl.cellClicked.connect(self.select_transect)

        # Add transect data
        for row in range(nrows):
            col = 0
            transect_id = row
            # checked = QtWidgets.QTableWidgetItem('')
            # checked.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            # if parent.meas.transects[row].checked:
            #     checked.setCheckState(QtCore.Qt.Checked)
            # else:
            #     checked.setCheckState(QtCore.Qt.Unchecked)
            # checked.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            # tbl.setItem(row, col, checked)
            # col += 1

            checked = QtWidgets.QTableWidgetItem(parent.meas.transects[transect_id].file_name[:-4])
            checked.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            if parent.meas.transects[row].checked:
                checked.setCheckState(QtCore.Qt.Checked)
            else:
                checked.setCheckState(QtCore.Qt.Unchecked)
            checked.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            tbl.setItem(row, col, checked)
            # tbl.setItem(row, col, QtWidgets.QTableWidgetItem(parent.meas.transects[transect_id].file_name[:-4]))
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.utcfromtimestamp(
                parent.meas.transects[transect_id].date_time.start_serial_time), '%H:%M:%S')))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(parent.meas.transects[transect_id].start_edge[0]))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem(datetime.strftime(datetime.utcfromtimestamp(
                parent.meas.transects[transect_id].date_time.end_serial_time), '%H:%M:%S')))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:5.1f}'.format(
                parent.meas.transects[transect_id].date_time.transect_duration_sec)))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:8.2f}'.format(parent.meas.discharge[transect_id].total
                                                                              * units['Q'])))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(parent.meas.discharge[transect_id].top
                                                                              * units['Q'])))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(parent.meas.discharge[transect_id].middle
                                                                              * units['Q'])))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(parent.meas.discharge[transect_id].bottom
                                                                              * units['Q'])))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(parent.meas.discharge[transect_id].left
                                                                              * units['Q'])))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)
            col += 1
            tbl.setItem(row, col, QtWidgets.QTableWidgetItem('{:7.2f}'.format(parent.meas.discharge[transect_id].right
                                                                              * units['Q'])))
            tbl.item(row, col).setFlags(QtCore.Qt.ItemIsEnabled)

        tbl.resizeColumnsToContents()
        tbl.resizeRowsToContents()
