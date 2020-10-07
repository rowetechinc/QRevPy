# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wHSource.ui'
#
# Created by: PyQt5 UI code generator 5.13.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_h_source(object):
    def setupUi(self, h_source):
        h_source.setObjectName("h_source")
        h_source.resize(342, 155)
        self.gridLayout_2 = QtWidgets.QGridLayout(h_source)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gb_source = QtWidgets.QGroupBox(h_source)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.gb_source.setFont(font)
        self.gb_source.setObjectName("gb_source")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.gb_source)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.rb_internal = QtWidgets.QRadioButton(self.gb_source)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.rb_internal.setFont(font)
        self.rb_internal.setObjectName("rb_internal")
        self.verticalLayout_2.addWidget(self.rb_internal)
        self.rb_external = QtWidgets.QRadioButton(self.gb_source)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.rb_external.setFont(font)
        self.rb_external.setObjectName("rb_external")
        self.verticalLayout_2.addWidget(self.rb_external)
        self.gridLayout_3.addLayout(self.verticalLayout_2, 0, 0, 1, 1)
        self.horizontalLayout.addWidget(self.gb_source)
        self.gb_h_source = QtWidgets.QGroupBox(h_source)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.gb_h_source.setFont(font)
        self.gb_h_source.setObjectName("gb_h_source")
        self.gridLayout = QtWidgets.QGridLayout(self.gb_h_source)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.rb_all = QtWidgets.QRadioButton(self.gb_h_source)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.rb_all.setFont(font)
        self.rb_all.setChecked(True)
        self.rb_all.setObjectName("rb_all")
        self.verticalLayout.addWidget(self.rb_all)
        self.rb_transect = QtWidgets.QRadioButton(self.gb_h_source)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.rb_transect.setFont(font)
        self.rb_transect.setObjectName("rb_transect")
        self.verticalLayout.addWidget(self.rb_transect)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.horizontalLayout.addWidget(self.gb_h_source)
        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(h_source)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout_2.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(h_source)
        self.buttonBox.accepted.connect(h_source.accept)
        self.buttonBox.rejected.connect(h_source.reject)
        QtCore.QMetaObject.connectSlotsByName(h_source)

    def retranslateUi(self, h_source):
        _translate = QtCore.QCoreApplication.translate
        h_source.setWindowTitle(_translate("h_source", "Heading Source"))
        self.gb_source.setTitle(_translate("h_source", "Heading Source"))
        self.rb_internal.setText(_translate("h_source", "Internal"))
        self.rb_external.setText(_translate("h_source", "External"))
        self.gb_h_source.setTitle(_translate("h_source", "Apply To:"))
        self.rb_all.setText(_translate("h_source", "All Transects"))
        self.rb_transect.setText(_translate("h_source", "Transect Only"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    h_source = QtWidgets.QDialog()
    ui = Ui_h_source()
    ui.setupUi(h_source)
    h_source.show()
    sys.exit(app.exec_())
