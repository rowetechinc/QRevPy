from PyQt5 import QtWidgets, QtGui
from UI import wComment
from datetime import datetime
import getpass


class Comment(QtWidgets.QDialog, wComment.Ui_Comment):
    """Dialog to allow users to enter comments.

    Parameters
    ----------
    wComment.Ui_Comment : QDialog
        Dialog window with options for users

    Attributes
    ----------
    text: str
        Text in text edit box
    """

    def __init__(self, parent=None):
        super(Comment, self).__init__(parent)
        self.setupUi(self)

        # Set font
        font = QtGui.QFont()
        font.setPointSize(12)
        self.text_edit_comment.setFont(font)

        # Create and add default information
        time_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_name = getpass.getuser()
        self.text = '[' + time_stamp + ', ' + user_name + ']:  '
        self.text_edit_comment.setPlainText(self.text)

        self.text_edit_comment.setFocus()
        self.text_edit_comment.moveCursor(QtGui.QTextCursor.End)
