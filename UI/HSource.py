from PyQt5 import QtWidgets
from UI import wHSource


class HSource(QtWidgets.QDialog, wHSource.Ui_h_source):
    """Dialog to allow users to change heading source.

    Parameters
    ----------
    wHSource.Ui_h_source : QDialog
        Dialog window with options for users
    """

    def __init__(self, parent=None):
        super(HSource, self).__init__(parent)
        self.setupUi(self)
