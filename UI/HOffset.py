from PyQt5 import QtWidgets
from UI import wHOffset


class HOffset(QtWidgets.QDialog, wHOffset.Ui_hoffset):
    """Dialog to allow users to change heading offset.

    Parameters
    ----------
    wHOffset.Ui_hoffset : QDialog
        Dialog window to allow users to change heading offset
    """

    def __init__(self, parent=None):
        super(HOffset, self).__init__(parent)
        self.setupUi(self)
