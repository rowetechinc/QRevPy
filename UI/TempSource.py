from PyQt5 import QtWidgets
from UI import wTempSource


class TempSource(QtWidgets.QDialog, wTempSource.Ui_temp_source):
    """Dialog to allow users to change temperature source.

    Parameters
    ----------
    wTempSource.Ui_temp_source : QDialog
        Dialog window to allow users to change temperature source
    """

    def __init__(self, parent=None):
        """Initialize dialog
        """
        super(TempSource, self).__init__(parent)
        self.setupUi(self)
