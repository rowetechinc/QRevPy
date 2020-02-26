from PyQt5 import QtWidgets, QtGui, QtCore
from UI import wEdgeDist


class EdgeDist(QtWidgets.QDialog, wEdgeDist.Ui_edge_dist):
    """Dialog to allow users to change temperature source.

    Parameters
    ----------
    wEdgeDist.Ui_edge_dist : QDialog
        Dialog window to allow users to change the edge distance
    """

    def __init__(self, parent=None):
        super(EdgeDist, self).__init__(parent)
        self.setupUi(self)

        # set qlineedit to numbers only, 2 decimals, and 0 to 69.99 ppt
        # rx = QtCore.QRegExp("^[0-9]\d*(\.\d{1,3})$")
        # validator = QtGui.QRegExpValidator(rx, self)
        # self.ed_edge_dist.setValidator(validator)