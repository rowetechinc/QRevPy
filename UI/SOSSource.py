from PyQt5 import QtWidgets
from UI import wSOSSource


class SOSSource(QtWidgets.QDialog, wSOSSource.Ui_sos_source):
    """Dialog to allow users to change speed of sound source.

    Parameters
    ----------
    wSOSSource.Ui_sos_source : QDialog
        Dialog window to allow users to change speed of sound
    """

    def __init__(self, parent=None):
        super(SOSSource, self).__init__(parent)
        self.setupUi(self)