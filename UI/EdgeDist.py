from PyQt5 import QtWidgets
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
