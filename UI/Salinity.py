from PyQt5 import QtWidgets, QtGui, QtCore
from UI import wSalinity


class Salinity(QtWidgets.QDialog, wSalinity.Ui_salinity):
    """Dialog to allow users to change salinity.

    Parameters
    ----------
    wSalinity.Ui_salinity : QDialog
        Dialog window to allow users to change salinity
    """

    def __init__(self, parent=None):
        super(Salinity, self).__init__(parent)
        self.setupUi(self)

        # set qlineedit to numbers only, 2 decimals, and 0 to 69.99 ppt
        rx = QtCore.QRegExp("^([0-9]|[1-6][0-9])(\.\d{1,2})$")
        validator = QtGui.QRegExpValidator(rx, self)
        self.ed_salinity.setValidator(validator)
