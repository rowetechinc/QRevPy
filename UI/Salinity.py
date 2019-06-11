from PyQt5 import QtWidgets
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