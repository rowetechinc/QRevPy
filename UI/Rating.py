from PyQt5 import QtWidgets
from UI import wRating


class Rating(QtWidgets.QDialog, wRating.Ui_rating):
    """Dialog to allow users to set a user rating.

    Parameters
    ----------
    wDraft.Ui_draft : QDialog
        Dialog window to allow users to change draft
    """

    def __init__(self, parent=None):
        super(Rating, self).__init__(parent)
        self.setupUi(self)