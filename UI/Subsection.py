from PyQt5 import QtWidgets
from UI import wSubsection


class Subsection(QtWidgets.QDialog, wSubsection.Ui_subsection):
    """Dialog to allow users to change heading offset.

    Parameters
    ----------
    wSubsection.Ui_subsection : QDialog
        Dialog window to allow users to subsection in extrap
    """

    def __init__(self, parent=None):
        """Initialize dialog
        """
        super(Subsection, self).__init__(parent)
        self.setupUi(self)
