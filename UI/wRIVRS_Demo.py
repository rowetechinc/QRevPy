# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wRIVRS_Demo.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_RIVRS_Demo(object):
    def setupUi(self, RIVRS_Demo):
        RIVRS_Demo.setObjectName("RIVRS_Demo")
        RIVRS_Demo.resize(1164, 689)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        RIVRS_Demo.setFont(font)
        self.centralwidget = QtWidgets.QWidget(RIVRS_Demo)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.pb_load = QtWidgets.QPushButton(self.centralwidget)
        self.pb_load.setObjectName("pb_load")
        self.verticalLayout.addWidget(self.pb_load)
        self.gb_load = QtWidgets.QGroupBox(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.gb_load.setFont(font)
        self.gb_load.setObjectName("gb_load")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.gb_load)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.table_original = QtWidgets.QTableWidget(self.gb_load)
        self.table_original.setObjectName("table_original")
        self.table_original.setColumnCount(0)
        self.table_original.setRowCount(0)
        self.gridLayout_2.addWidget(self.table_original, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.gb_load)
        self.pb_qrev = QtWidgets.QPushButton(self.centralwidget)
        self.pb_qrev.setEnabled(False)
        self.pb_qrev.setObjectName("pb_qrev")
        self.verticalLayout.addWidget(self.pb_qrev)
        self.gb_ressults = QtWidgets.QGroupBox(self.centralwidget)
        self.gb_ressults.setObjectName("gb_ressults")
        self.gridLayout = QtWidgets.QGridLayout(self.gb_ressults)
        self.gridLayout.setObjectName("gridLayout")
        self.table_processed = QtWidgets.QTableWidget(self.gb_ressults)
        self.table_processed.setObjectName("table_processed")
        self.table_processed.setColumnCount(0)
        self.table_processed.setRowCount(0)
        self.gridLayout.addWidget(self.table_processed, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.gb_ressults)
        self.gridLayout_3.addLayout(self.verticalLayout, 0, 0, 1, 1)
        RIVRS_Demo.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(RIVRS_Demo)
        self.statusbar.setObjectName("statusbar")
        RIVRS_Demo.setStatusBar(self.statusbar)

        self.retranslateUi(RIVRS_Demo)
        QtCore.QMetaObject.connectSlotsByName(RIVRS_Demo)

    def retranslateUi(self, RIVRS_Demo):
        _translate = QtCore.QCoreApplication.translate
        RIVRS_Demo.setWindowTitle(_translate("RIVRS_Demo", "RIVRS_Demo"))
        self.pb_load.setText(_translate("RIVRS_Demo", "Load Data"))
        self.gb_load.setTitle(_translate("RIVRS_Demo", "Loaded Data"))
        self.pb_qrev.setText(_translate("RIVRS_Demo", "Run QRev"))
        self.gb_ressults.setTitle(_translate("RIVRS_Demo", "Final Measurements"))




if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    RIVRS_Demo = QtWidgets.QMainWindow()
    ui = Ui_RIVRS_Demo()
    ui.setupUi(RIVRS_Demo)
    RIVRS_Demo.show()
    sys.exit(app.exec_())
