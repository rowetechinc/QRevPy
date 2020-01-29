from PyQt5 import QtWidgets, QtGui, QtCore
from UI import wEdgeEns


class EdgeEns(QtWidgets.QDialog, wEdgeEns.Ui_edge_ens):
    """Dialog to allow users to change temperature source.

    Parameters
    ----------
    wEdgeEns.Ui_edge_ens : QDialog
        Dialog window to allow users to change the number of ensembles in an edge
    """

    def __init__(self, parent=None):
        super(EdgeEns, self).__init__(parent)
        self.setupUi(self)

        # set qlineedit to numbers only, 2 decimals, and 0 to 69.99 ppt
        rx = QtCore.QRegExp("^[0-9]\d+$")
        validator = QtGui.QRegExpValidator(rx, self)
        self.ed_edge_ens.setValidator(validator)
