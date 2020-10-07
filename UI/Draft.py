from PyQt5 import QtWidgets
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
