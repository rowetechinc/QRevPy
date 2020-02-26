from PyQt5 import QtWidgets, QtCore, QtGui
from UI import wDraft


class Draft(QtWidgets.QDialog, wDraft.Ui_draft):
    """Dialog to allow users to change draft.

    Parameters
    ----------
    wDraft.Ui_draft : QDialog
        Dialog window to allow users to change draft
    """

    def __init__(self, parent=None):
        super(Draft, self).__init__(parent)
        self.setupUi(self)

        # set qlineedit to numbers only, 2 decimals
        # rx = QtCore.QRegExp("^[0-9]\d*(\.\d{1,2})$")
        # validator = QtGui.QRegExpValidator(rx, self)
        # self.ed_draft.setValidator(validator)