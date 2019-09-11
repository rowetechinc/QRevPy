from PyQt5 import QtWidgets
from UI import wStartEdge


class StartEdge(QtWidgets.QDialog, wStartEdge.Ui_start_edge):
    """Dialog to allow users to change temperature source.

    Parameters
    ----------
    wStartEdge.Ui_start_edge : QDialog
        Dialog window to allow users to change start edge
    """

    def __init__(self, parent=None):
        super(StartEdge, self).__init__(parent)
        self.setupUi(self)