from PyQt5 import QtWidgets
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