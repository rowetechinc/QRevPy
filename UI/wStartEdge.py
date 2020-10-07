# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wStartEdge.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_start_edge(object):
    def setupUi(self, start_edge):
        start_edge.setObjectName("start_edge")
        start_edge.resize(146, 120)
        self.gridLayout_2 = QtWidgets.QGridLayout(start_edge)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gb_start_edge = QtWidgets.QGroupBox(start_edge)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.gb_start_edge.setFont(font)
        self.gb_start_edge.setObjectName("gb_start_edge")
        self.gridLayout = QtWidgets.QGridLayout(self.gb_start_edge)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.rb_left = QtWidgets.QRadioButton(self.gb_start_edge)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.rb_left.setFont(font)
        self.rb_left.setChecked(True)
        self.rb_left.setObjectName("rb_left")
        self.verticalLayout.addWidget(self.rb_left)
        self.rb_right = QtWidgets.QRadioButton(self.gb_start_edge)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.rb_right.setFont(font)
        self.rb_right.setObjectName("rb_right")
        self.verticalLayout.addWidget(self.rb_right)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.horizontalLayout.addWidget(self.gb_start_edge)
        self.horizontalLayout.setStretch(0, 1)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(start_edge)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_3.addWidget(self.buttonBox)
        self.gridLayout_2.addLayout(self.verticalLayout_3, 0, 0, 1, 1)

        self.retranslateUi(start_edge)
        self.buttonBox.accepted.connect(start_edge.accept)
        self.buttonBox.rejected.connect(start_edge.reject)
        QtCore.QMetaObject.connectSlotsByName(start_edge)

    def retranslateUi(self, start_edge):
        _translate = QtCore.QCoreApplication.translate
        start_edge.setWindowTitle(_translate("start_edge", "Start Edge"))
        self.gb_start_edge.setTitle(_translate("start_edge", "Start Edge:"))
        self.rb_left.setText(_translate("start_edge", "Left"))
        self.rb_right.setText(_translate("start_edge", "Right"))




if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    start_edge = QtWidgets.QDialog()
    ui = Ui_start_edge()
    ui.setupUi(start_edge)
    start_edge.show()
    sys.exit(app.exec_())
