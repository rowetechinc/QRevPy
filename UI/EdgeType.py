from PyQt5 import QtWidgets, QtGui, QtCore
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

        # set custom qlineedit to numbers only, 4 decimals, and 0 to 9
        rx_custom = QtCore.QRegExp("^([0-9])(\.\d{1,4})$")
        validator_custom = QtGui.QRegExpValidator(rx_custom, self)
        self.ed_custom.setValidator(validator_custom)

        # set user q qlineedit to numbers only
        rx_q = QtCore.QRegExp("^[-}?[0-9]\d*(\.\d+)?$")
        validator_q = QtGui.QRegExpValidator(rx_q, self)
        self.ed_q_user.setValidator(validator_q)
