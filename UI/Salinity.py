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

        # set qlineedit to numbers only
        rx = QtCore.QRegExp("^(?:(?:\d|[1-9]\d)(?:\.[00]0?)?|60(?:\.00?)?)$")
        validator = QtGui.QRegExpValidator(rx, self)
        self.ed_salinity.setValidator(validator)
