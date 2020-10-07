# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wComment.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Comment(object):
    def setupUi(self, Comment):
        Comment.setObjectName("Comment")
        Comment.setWindowModality(QtCore.Qt.ApplicationModal)
        Comment.resize(643, 172)
        self.buttonBox = QtWidgets.QDialogButtonBox(Comment)
        self.buttonBox.setGeometry(QtCore.QRect(270, 120, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.text_edit_comment = QtWidgets.QPlainTextEdit(Comment)
        self.text_edit_comment.setGeometry(QtCore.QRect(10, 10, 611, 101))
        self.text_edit_comment.setObjectName("text_edit_comment")

        self.retranslateUi(Comment)
        self.buttonBox.accepted.connect(Comment.accept)
        self.buttonBox.rejected.connect(Comment.reject)
        QtCore.QMetaObject.connectSlotsByName(Comment)


    def retranslateUi(self, Comment):
        _translate = QtCore.QCoreApplication.translate
        Comment.setWindowTitle(_translate("Comment", "Enter Comment"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Comment = QtWidgets.QDialog()
    ui = Ui_Comment()
    ui.setupUi(Comment)
    Comment.show()
    sys.exit(app.exec_())

