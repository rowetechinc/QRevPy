from PyQt5 import QtWidgets
from UI import wEdgeType


class EdgeType(QtWidgets.QDialog, wEdgeType.Ui_edge_type):
    """Dialog to allow users to change temperature source.

    Parameters
    ----------
    wEdgeType.Ui_edge_type : QDialog
        Dialog window to allow users to change edge type
    """

    def __init__(self, parent=None):
        super(EdgeType, self).__init__(parent)
        self.setupUi(self)