from PyQt5 import QtWidgets
from UI import wMagVar


class MagVar(QtWidgets.QDialog, wMagVar.Ui_mag_var):
    """Dialog to allow users to change magvar.

    Parameters
    ----------
    wMagVar.Ui_mag_var : QDialog
        Dialog window to allow users to change magvar
    """

    def __init__(self, parent=None):
        super(MagVar, self).__init__(parent)
        self.setupUi(self)
