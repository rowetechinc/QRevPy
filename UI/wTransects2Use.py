# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wTransects2Use.ui'
#
# Created by: PyQt5 UI code generator 5.13.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Transects2Use(object):
    def setupUi(self, Transects2Use):
        Transects2Use.setObjectName("Transects2Use")
        Transects2Use.setWindowModality(QtCore.Qt.ApplicationModal)
        Transects2Use.resize(864, 270)
        self.gridLayout = QtWidgets.QGridLayout(Transects2Use)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.tableSelect = QtWidgets.QTableWidget(Transects2Use)
        self.tableSelect.setObjectName("tableSelect")
        self.tableSelect.setColumnCount(0)
        self.tableSelect.setRowCount(0)
        self.verticalLayout.addWidget(self.tableSelect)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pb_check_all = QtWidgets.QPushButton(Transects2Use)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.pb_check_all.setFont(font)
        self.pb_check_all.setObjectName("pb_check_all")
        self.horizontalLayout.addWidget(self.pb_check_all)
        self.pb_uncheck_all = QtWidgets.QPushButton(Transects2Use)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.pb_uncheck_all.setFont(font)
        self.pb_uncheck_all.setObjectName("pb_uncheck_all")
        self.horizontalLayout.addWidget(self.pb_uncheck_all)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.buttonBox = QtWidgets.QDialogButtonBox(Transects2Use)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.buttonBox.setFont(font)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(Transects2Use)
        self.buttonBox.accepted.connect(Transects2Use.accept)
        self.buttonBox.rejected.connect(Transects2Use.reject)
        QtCore.QMetaObject.connectSlotsByName(Transects2Use)

    def retranslateUi(self, Transects2Use):
        _translate = QtCore.QCoreApplication.translate
        Transects2Use.setWindowTitle(_translate("Transects2Use", "Transects to Use"))
        self.pb_check_all.setText(_translate("Transects2Use", "Check All"))
        self.pb_uncheck_all.setText(_translate("Transects2Use", "Uncheck All"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Transects2Use = QtWidgets.QDialog()
    ui = Ui_Transects2Use()
    ui.setupUi(Transects2Use)
    Transects2Use.show()
    sys.exit(app.exec_())
