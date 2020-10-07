# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wEdgeEns.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_edge_ens(object):
    def setupUi(self, edge_ens):
        edge_ens.setObjectName("edge_ens")
        edge_ens.resize(277, 120)
        self.gridLayout_2 = QtWidgets.QGridLayout(edge_ens)
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
        self.edge_ens_label = QtWidgets.QLabel(edge_ens)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.edge_ens_label.setFont(font)
        self.edge_ens_label.setObjectName("edge_ens_label")
        self.horizontalLayout_2.addWidget(self.edge_ens_label)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)
        self.ed_edge_ens = QtWidgets.QLineEdit(edge_ens)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.ed_edge_ens.setFont(font)
        self.ed_edge_ens.setObjectName("ed_edge_ens")
        self.horizontalLayout.addWidget(self.ed_edge_ens)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem4)
        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 1)
        self.horizontalLayout.setStretch(2, 2)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        spacerItem5 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem5)
        self.horizontalLayout_3.addLayout(self.verticalLayout_2)
        self.gb_apply_to = QtWidgets.QGroupBox(edge_ens)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.gb_apply_to.setFont(font)
        self.gb_apply_to.setObjectName("gb_apply_to")
        self.gridLayout = QtWidgets.QGridLayout(self.gb_apply_to)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.rb_all = QtWidgets.QRadioButton(self.gb_apply_to)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.rb_all.setFont(font)
        self.rb_all.setChecked(True)
        self.rb_all.setObjectName("rb_all")
        self.verticalLayout.addWidget(self.rb_all)
        self.rb_transect = QtWidgets.QRadioButton(self.gb_apply_to)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.rb_transect.setFont(font)
        self.rb_transect.setObjectName("rb_transect")
        self.verticalLayout.addWidget(self.rb_transect)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.horizontalLayout_3.addWidget(self.gb_apply_to)
        self.gridLayout_2.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(edge_ens)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout_2.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(edge_ens)
        self.buttonBox.accepted.connect(edge_ens.accept)
        self.buttonBox.rejected.connect(edge_ens.reject)
        QtCore.QMetaObject.connectSlotsByName(edge_ens)

    def retranslateUi(self, edge_ens):
        _translate = QtCore.QCoreApplication.translate
        edge_ens.setWindowTitle(_translate("edge_ens", "Edge Ensembles"))
        self.edge_ens_label.setText(_translate("edge_ens", "Number of Edge Ensembles"))
        self.gb_apply_to.setTitle(_translate("edge_ens", "Apply To:"))
        self.rb_all.setText(_translate("edge_ens", "All Transects"))
        self.rb_transect.setText(_translate("edge_ens", "Transect Only"))




if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    edge_ens = QtWidgets.QDialog()
    ui = Ui_edge_ens()
    ui.setupUi(edge_ens)
    edge_ens.show()
    sys.exit(app.exec_())
