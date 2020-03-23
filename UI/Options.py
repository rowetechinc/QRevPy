from PyQt5 import QtWidgets, QtGui
from UI import wOptions


class Options(QtWidgets.QDialog, wOptions.Ui_Options):
    """Dialog to allow users to change QRev options.

    Parameters
    ----------
    wOptions.Ui_Options : QDialog
        Dialog window with options for users
    """

    def __init__(self, parent=None):
        """Initialize options dialog.
        """
        super(Options, self).__init__(parent)
        self.setupUi(self)

        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)

        self.rb_All.setFont(font)
        self.rb_checked.setFont(font)
        self.rb_english.setFont(font)
        self.rb_si.setFont(font)
        self.cb_stylesheet.setFont(font)
