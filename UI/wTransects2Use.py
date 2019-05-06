# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wTransects2Use.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Transects2Use(object):
    def setupUi(self, Transects2Use):
        Transects2Use.setObjectName("Transects2Use")
        Transects2Use.setWindowModality(QtCore.Qt.ApplicationModal)
        Transects2Use.resize(864, 245)
        self.verticalLayout = QtWidgets.QVBoxLayout(Transects2Use)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tableSelect = QtWidgets.QTableWidget(Transects2Use)
        self.tableSelect.setObjectName("tableSelect")
        self.tableSelect.setColumnCount(0)
        self.tableSelect.setRowCount(0)
        self.verticalLayout.addWidget(self.tableSelect)
        self.buttonBox = QtWidgets.QDialogButtonBox(Transects2Use)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Transects2Use)
        self.buttonBox.accepted.connect(Transects2Use.accept)
        self.buttonBox.rejected.connect(Transects2Use.reject)
        QtCore.QMetaObject.connectSlotsByName(Transects2Use)

    def retranslateUi(self, Transects2Use):
        _translate = QtCore.QCoreApplication.translate
        Transects2Use.setWindowTitle(_translate("Transects2Use", "Transects to Use"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Transects2Use = QtWidgets.QDialog()
    ui = Ui_Transects2Use()
    ui.setupUi(Transects2Use)
    Transects2Use.show()
    sys.exit(app.exec_())

