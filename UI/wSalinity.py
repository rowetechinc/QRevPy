# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wSalinity.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_salinity(object):
    def setupUi(self, salinity):
        salinity.setObjectName("salinity")
        salinity.resize(342, 155)
        self.gridLayout_2 = QtWidgets.QGridLayout(salinity)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.salinity_label = QtWidgets.QLabel(salinity)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.salinity_label.setFont(font)
        self.salinity_label.setObjectName("salinity_label")
        self.horizontalLayout_2.addWidget(self.salinity_label)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)
        self.ed_salinity = QtWidgets.QLineEdit(salinity)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.ed_salinity.setFont(font)
        self.ed_salinity.setObjectName("ed_salinity")
        self.horizontalLayout.addWidget(self.ed_salinity)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem4)
        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 1)
        self.horizontalLayout.setStretch(2, 2)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        spacerItem5 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem5)
        self.horizontalLayout_3.addLayout(self.verticalLayout_2)
        self.gb_magvar = QtWidgets.QGroupBox(salinity)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.gb_magvar.setFont(font)
        self.gb_magvar.setObjectName("gb_magvar")
        self.gridLayout = QtWidgets.QGridLayout(self.gb_magvar)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.rb_all = QtWidgets.QRadioButton(self.gb_magvar)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.rb_all.setFont(font)
        self.rb_all.setChecked(True)
        self.rb_all.setObjectName("rb_all")
        self.verticalLayout.addWidget(self.rb_all)
        self.rb_transect = QtWidgets.QRadioButton(self.gb_magvar)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.rb_transect.setFont(font)
        self.rb_transect.setObjectName("rb_transect")
        self.verticalLayout.addWidget(self.rb_transect)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.horizontalLayout_3.addWidget(self.gb_magvar)
        self.gridLayout_2.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(salinity)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout_2.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(salinity)
        self.buttonBox.accepted.connect(salinity.accept)
        self.buttonBox.rejected.connect(salinity.reject)
        QtCore.QMetaObject.connectSlotsByName(salinity)

    def retranslateUi(self, salinity):
        _translate = QtCore.QCoreApplication.translate
        salinity.setWindowTitle(_translate("salinity", "Salinity"))
        self.salinity_label.setText(_translate("salinity", "Salinity (ppt)"))
        self.gb_magvar.setTitle(_translate("salinity", "Apply To:"))
        self.rb_all.setText(_translate("salinity", "All Transects"))
        self.rb_transect.setText(_translate("salinity", "Transect Only"))




if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    salinity = QtWidgets.QDialog()
    ui = Ui_salinity()
    ui.setupUi(salinity)
    salinity.show()
    sys.exit(app.exec_())
