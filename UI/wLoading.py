# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wLoading.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Loading_Message(object):
    def setupUi(self, Loading_Message):
        Loading_Message.setObjectName("Loading_Message")
        Loading_Message.setEnabled(True)
        Loading_Message.resize(541, 174)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/24x24/Info.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Loading_Message.setWindowIcon(icon)
        self.message = QtWidgets.QLabel(Loading_Message)
        self.message.setGeometry(QtCore.QRect(30, 0, 461, 171))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.message.setFont(font)
        self.message.setObjectName("message")

        self.retranslateUi(Loading_Message)
        QtCore.QMetaObject.connectSlotsByName(Loading_Message)

    def retranslateUi(self, Loading_Message):
        _translate = QtCore.QCoreApplication.translate
        Loading_Message.setWindowTitle(_translate("Loading_Message", "Loading Measurement"))
        self.message.setText(_translate("Loading_Message", "<html><head/><body><p align=\"center\">QRev is loading and processing the measurement files.<br/></p><p align=\"center\">This window will close automatically </p><p align=\"center\">when the processing is complete</p></body></html>"))

import dsm_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Loading_Message = QtWidgets.QDialog()
    ui = Ui_Loading_Message()
    ui.setupUi(Loading_Message)
    Loading_Message.show()
    sys.exit(app.exec_())

