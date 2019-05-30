from PyQt5 import QtWidgets, QtGui
from UI import wLoading

class Loading(QtWidgets.QDialog, wLoading.Ui_Loading_Message):
    """Dialog to allow users to change QRev options.

    Parameters
    ----------
    wOptions.Ui_Options : QDialog
        Dialog window with options for users
    """

    def __init__(self, parent=None):
        super(Loading, self).__init__(parent)
        self.setupUi(self)