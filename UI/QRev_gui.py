# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'QRev_gui.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1074, 700)
        MainWindow.setLayoutDirection(QtCore.Qt.LeftToRight)
        MainWindow.setDockOptions(QtWidgets.QMainWindow.AllowTabbedDocks|QtWidgets.QMainWindow.AnimatedDocks|QtWidgets.QMainWindow.VerticalTabs)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.tab_all = QtWidgets.QTabWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tab_all.sizePolicy().hasHeightForWidth())
        self.tab_all.setSizePolicy(sizePolicy)
        self.tab_all.setSizeIncrement(QtCore.QSize(0, 0))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.tab_all.setFont(font)
        self.tab_all.setAutoFillBackground(False)
        self.tab_all.setTabPosition(QtWidgets.QTabWidget.North)
        self.tab_all.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tab_all.setIconSize(QtCore.QSize(40, 24))
        self.tab_all.setObjectName("tab_all")
        self.tab_main = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tab_main.sizePolicy().hasHeightForWidth())
        self.tab_main.setSizePolicy(sizePolicy)
        self.tab_main.setObjectName("tab_main")
        self.gridLayout = QtWidgets.QGridLayout(self.tab_main)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.tab_summary = QtWidgets.QTabWidget(self.tab_main)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)
        self.tab_summary.setPalette(palette)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.tab_summary.setFont(font)
        self.tab_summary.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.tab_summary.setTabPosition(QtWidgets.QTabWidget.North)
        self.tab_summary.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tab_summary.setObjectName("tab_summary")
        self.tab_summary_discharge = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tab_summary_discharge.sizePolicy().hasHeightForWidth())
        self.tab_summary_discharge.setSizePolicy(sizePolicy)
        self.tab_summary_discharge.setObjectName("tab_summary_discharge")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tab_summary_discharge)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.main_table_summary = QtWidgets.QTableWidget(self.tab_summary_discharge)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.main_table_summary.setFont(font)
        self.main_table_summary.setAutoFillBackground(False)
        self.main_table_summary.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
        self.main_table_summary.setObjectName("main_table_summary")
        self.main_table_summary.setColumnCount(0)
        self.main_table_summary.setRowCount(0)
        self.gridLayout_2.addWidget(self.main_table_summary, 0, 0, 1, 1)
        self.tab_summary.addTab(self.tab_summary_discharge, "")
        self.tab_summary_details = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tab_summary_details.sizePolicy().hasHeightForWidth())
        self.tab_summary_details.setSizePolicy(sizePolicy)
        self.tab_summary_details.setObjectName("tab_summary_details")
        self.tab_summary.addTab(self.tab_summary_details, "")
        self.tab_summary_premeasurement = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tab_summary_premeasurement.sizePolicy().hasHeightForWidth())
        self.tab_summary_premeasurement.setSizePolicy(sizePolicy)
        self.tab_summary_premeasurement.setObjectName("tab_summary_premeasurement")
        self.tab_summary.addTab(self.tab_summary_premeasurement, "")
        self.tab_summary_settings = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tab_summary_settings.sizePolicy().hasHeightForWidth())
        self.tab_summary_settings.setSizePolicy(sizePolicy)
        self.tab_summary_settings.setObjectName("tab_summary_settings")
        self.tab_summary.addTab(self.tab_summary_settings, "")
        self.verticalLayout.addWidget(self.tab_summary)
        self.graphics_main_middle = QtWidgets.QWidget(self.tab_main)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.graphics_main_middle.sizePolicy().hasHeightForWidth())
        self.graphics_main_middle.setSizePolicy(sizePolicy)
        self.graphics_main_middle.setMinimumSize(QtCore.QSize(500, 200))
        self.graphics_main_middle.setAutoFillBackground(True)
        self.graphics_main_middle.setObjectName("graphics_main_middle")
        self.verticalLayout.addWidget(self.graphics_main_middle)
        self.horizontalLayout_bottom = QtWidgets.QHBoxLayout()
        self.horizontalLayout_bottom.setObjectName("horizontalLayout_bottom")
        self.tab_mc = QtWidgets.QTabWidget(self.tab_main)
        self.tab_mc.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tab_mc.setObjectName("tab_mc")
        self.tab_mc_messages = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tab_mc_messages.sizePolicy().hasHeightForWidth())
        self.tab_mc_messages.setSizePolicy(sizePolicy)
        self.tab_mc_messages.setObjectName("tab_mc_messages")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.tab_mc_messages)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.main_message_table = QtWidgets.QTableWidget(self.tab_mc_messages)
        self.main_message_table.setObjectName("main_message_table")
        self.main_message_table.setColumnCount(0)
        self.main_message_table.setRowCount(0)
        self.gridLayout_3.addWidget(self.main_message_table, 0, 0, 1, 1)
        self.tab_mc.addTab(self.tab_mc_messages, "")
        self.tab_mc_comments = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tab_mc_comments.sizePolicy().hasHeightForWidth())
        self.tab_mc_comments.setSizePolicy(sizePolicy)
        self.tab_mc_comments.setObjectName("tab_mc_comments")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.tab_mc_comments)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.display_comments = QtWidgets.QPlainTextEdit(self.tab_mc_comments)
        self.display_comments.setReadOnly(True)
        self.display_comments.setObjectName("display_comments")
        self.horizontalLayout_2.addWidget(self.display_comments)
        self.tab_mc.addTab(self.tab_mc_comments, "")
        self.horizontalLayout_bottom.addWidget(self.tab_mc)
        self.graphics_main_timeseries = QtWidgets.QWidget(self.tab_main)
        self.graphics_main_timeseries.setObjectName("graphics_main_timeseries")
        self.horizontalLayout_bottom.addWidget(self.graphics_main_timeseries)
        self.horizontalLayout_bottom.setStretch(0, 4)
        self.horizontalLayout_bottom.setStretch(1, 2)
        self.verticalLayout.addLayout(self.horizontalLayout_bottom)
        self.verticalLayout.setStretch(0, 2)
        self.verticalLayout.setStretch(1, 2)
        self.verticalLayout.setStretch(2, 2)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_right = QtWidgets.QVBoxLayout()
        self.verticalLayout_right.setObjectName("verticalLayout_right")
        self.table_qa = QtWidgets.QTableWidget(self.tab_main)
        self.table_qa.setObjectName("table_qa")
        self.table_qa.setColumnCount(0)
        self.table_qa.setRowCount(0)
        self.verticalLayout_right.addWidget(self.table_qa)
        self.table_uncertainty = QtWidgets.QTableWidget(self.tab_main)
        self.table_uncertainty.setObjectName("table_uncertainty")
        self.table_uncertainty.setColumnCount(0)
        self.table_uncertainty.setRowCount(0)
        self.verticalLayout_right.addWidget(self.table_uncertainty)
        self.graphics_main_extrap = QtWidgets.QWidget(self.tab_main)
        self.graphics_main_extrap.setObjectName("graphics_main_extrap")
        self.verticalLayout_right.addWidget(self.graphics_main_extrap)
        self.verticalLayout_right.setStretch(0, 3)
        self.verticalLayout_right.setStretch(1, 5)
        self.verticalLayout_right.setStretch(2, 6)
        self.horizontalLayout.addLayout(self.verticalLayout_right)
        self.horizontalLayout.setStretch(0, 8)
        self.horizontalLayout.setStretch(1, 2)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.tab_all.addTab(self.tab_main, "")
        self.tab_systest = QtWidgets.QWidget()
        self.tab_systest.setObjectName("tab_systest")
        self.tab_systest_2 = QtWidgets.QTabWidget(self.tab_systest)
        self.tab_systest_2.setGeometry(QtCore.QRect(2, 9, 991, 581))
        self.tab_systest_2.setTabPosition(QtWidgets.QTabWidget.North)
        self.tab_systest_2.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tab_systest_2.setObjectName("tab_systest_2")
        self.tab_systest_2_results = QtWidgets.QWidget()
        self.tab_systest_2_results.setObjectName("tab_systest_2_results")
        self.tab_systest_2.addTab(self.tab_systest_2_results, "")
        self.tab_systest_2_messages = QtWidgets.QWidget()
        self.tab_systest_2_messages.setObjectName("tab_systest_2_messages")
        self.tab_systest_2.addTab(self.tab_systest_2_messages, "")
        self.tab_all.addTab(self.tab_systest, "")
        self.tab_compass = QtWidgets.QWidget()
        self.tab_compass.setObjectName("tab_compass")
        self.tab_compass_2 = QtWidgets.QTabWidget(self.tab_compass)
        self.tab_compass_2.setGeometry(QtCore.QRect(0, 10, 1161, 581))
        self.tab_compass_2.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tab_compass_2.setObjectName("tab_compass_2")
        self.tab_compass_2_data = QtWidgets.QWidget()
        self.tab_compass_2_data.setObjectName("tab_compass_2_data")
        self.tab_compass_2.addTab(self.tab_compass_2_data, "")
        self.tab_compass_2_cal = QtWidgets.QWidget()
        self.tab_compass_2_cal.setObjectName("tab_compass_2_cal")
        self.tab_compass_2.addTab(self.tab_compass_2_cal, "")
        self.tab_compass_2_messages = QtWidgets.QWidget()
        self.tab_compass_2_messages.setObjectName("tab_compass_2_messages")
        self.tab_compass_2.addTab(self.tab_compass_2_messages, "")
        self.tab_all.addTab(self.tab_compass, "")
        self.tab_tempsal = QtWidgets.QWidget()
        self.tab_tempsal.setObjectName("tab_tempsal")
        self.tab_tempsal_2 = QtWidgets.QTabWidget(self.tab_tempsal)
        self.tab_tempsal_2.setGeometry(QtCore.QRect(0, 10, 1221, 571))
        self.tab_tempsal_2.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tab_tempsal_2.setObjectName("tab_tempsal_2")
        self.tab_tempsal_2_data = QtWidgets.QWidget()
        self.tab_tempsal_2_data.setObjectName("tab_tempsal_2_data")
        self.tab_tempsal_2.addTab(self.tab_tempsal_2_data, "")
        self.tab_tempsal_2_messages = QtWidgets.QWidget()
        self.tab_tempsal_2_messages.setObjectName("tab_tempsal_2_messages")
        self.tab_tempsal_2.addTab(self.tab_tempsal_2_messages, "")
        self.tab_all.addTab(self.tab_tempsal, "")
        self.tab_mbt = QtWidgets.QWidget()
        self.tab_mbt.setObjectName("tab_mbt")
        self.tab_mtb_2 = QtWidgets.QTabWidget(self.tab_mbt)
        self.tab_mtb_2.setGeometry(QtCore.QRect(0, 10, 1231, 571))
        self.tab_mtb_2.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tab_mtb_2.setObjectName("tab_mtb_2")
        self.tab_mbt_2_data = QtWidgets.QWidget()
        self.tab_mbt_2_data.setObjectName("tab_mbt_2_data")
        self.tab_mtb_2.addTab(self.tab_mbt_2_data, "")
        self.tab_mbt_2_messages = QtWidgets.QWidget()
        self.tab_mbt_2_messages.setObjectName("tab_mbt_2_messages")
        self.tab_mtb_2.addTab(self.tab_mbt_2_messages, "")
        self.tab_all.addTab(self.tab_mbt, "")
        self.tab_bt = QtWidgets.QWidget()
        self.tab_bt.setObjectName("tab_bt")
        self.tab_bt_2 = QtWidgets.QTabWidget(self.tab_bt)
        self.tab_bt_2.setGeometry(QtCore.QRect(0, 0, 1231, 601))
        self.tab_bt_2.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tab_bt_2.setObjectName("tab_bt_2")
        self.tab_bt_2_data = QtWidgets.QWidget()
        self.tab_bt_2_data.setObjectName("tab_bt_2_data")
        self.tab_bt_2.addTab(self.tab_bt_2_data, "")
        self.tab_bt_2_messages = QtWidgets.QWidget()
        self.tab_bt_2_messages.setObjectName("tab_bt_2_messages")
        self.tab_bt_2.addTab(self.tab_bt_2_messages, "")
        self.tab_all.addTab(self.tab_bt, "")
        self.tab_gps = QtWidgets.QWidget()
        self.tab_gps.setObjectName("tab_gps")
        self.tab_gps_2 = QtWidgets.QTabWidget(self.tab_gps)
        self.tab_gps_2.setGeometry(QtCore.QRect(0, 0, 1231, 601))
        self.tab_gps_2.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tab_gps_2.setObjectName("tab_gps_2")
        self.tab_gps_2_data = QtWidgets.QWidget()
        self.tab_gps_2_data.setObjectName("tab_gps_2_data")
        self.tab_gps_2.addTab(self.tab_gps_2_data, "")
        self.tab_gps_2_messages_2 = QtWidgets.QWidget()
        self.tab_gps_2_messages_2.setObjectName("tab_gps_2_messages_2")
        self.tab_gps_2.addTab(self.tab_gps_2_messages_2, "")
        self.tab_all.addTab(self.tab_gps, "")
        self.tab_depth = QtWidgets.QWidget()
        self.tab_depth.setObjectName("tab_depth")
        self.tab_depth_2 = QtWidgets.QTabWidget(self.tab_depth)
        self.tab_depth_2.setGeometry(QtCore.QRect(0, 0, 1231, 601))
        self.tab_depth_2.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tab_depth_2.setObjectName("tab_depth_2")
        self.tab_depth_2_data = QtWidgets.QWidget()
        self.tab_depth_2_data.setObjectName("tab_depth_2_data")
        self.tab_depth_2.addTab(self.tab_depth_2_data, "")
        self.tab_gps_2_messages_3 = QtWidgets.QWidget()
        self.tab_gps_2_messages_3.setObjectName("tab_gps_2_messages_3")
        self.tab_depth_2.addTab(self.tab_gps_2_messages_3, "")
        self.tab_all.addTab(self.tab_depth, "")
        self.tab_wt = QtWidgets.QWidget()
        self.tab_wt.setObjectName("tab_wt")
        self.tab_wt_2 = QtWidgets.QTabWidget(self.tab_wt)
        self.tab_wt_2.setGeometry(QtCore.QRect(0, 0, 1231, 601))
        self.tab_wt_2.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tab_wt_2.setObjectName("tab_wt_2")
        self.tab_wt_2_data = QtWidgets.QWidget()
        self.tab_wt_2_data.setObjectName("tab_wt_2_data")
        self.tab_wt_2.addTab(self.tab_wt_2_data, "")
        self.tab_wt_2_messages = QtWidgets.QWidget()
        self.tab_wt_2_messages.setObjectName("tab_wt_2_messages")
        self.tab_wt_2.addTab(self.tab_wt_2_messages, "")
        self.tab_all.addTab(self.tab_wt, "")
        self.tab_extrap = QtWidgets.QWidget()
        self.tab_extrap.setObjectName("tab_extrap")
        self.tab_extrap_2 = QtWidgets.QTabWidget(self.tab_extrap)
        self.tab_extrap_2.setGeometry(QtCore.QRect(0, 0, 1231, 601))
        self.tab_extrap_2.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tab_extrap_2.setObjectName("tab_extrap_2")
        self.tab_extrap_2_data = QtWidgets.QWidget()
        self.tab_extrap_2_data.setObjectName("tab_extrap_2_data")
        self.tab_extrap_2.addTab(self.tab_extrap_2_data, "")
        self.tab_wt_2_messages_2 = QtWidgets.QWidget()
        self.tab_wt_2_messages_2.setObjectName("tab_wt_2_messages_2")
        self.tab_extrap_2.addTab(self.tab_wt_2_messages_2, "")
        self.tab_all.addTab(self.tab_extrap, "")
        self.tab_edges = QtWidgets.QWidget()
        self.tab_edges.setObjectName("tab_edges")
        self.tab_edges_2 = QtWidgets.QTabWidget(self.tab_edges)
        self.tab_edges_2.setGeometry(QtCore.QRect(0, 0, 1231, 601))
        self.tab_edges_2.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tab_edges_2.setObjectName("tab_edges_2")
        self.tab_edges_2_data = QtWidgets.QWidget()
        self.tab_edges_2_data.setObjectName("tab_edges_2_data")
        self.tab_edges_2.addTab(self.tab_edges_2_data, "")
        self.tab_wt_2_messages_3 = QtWidgets.QWidget()
        self.tab_wt_2_messages_3.setObjectName("tab_wt_2_messages_3")
        self.tab_edges_2.addTab(self.tab_wt_2_messages_3, "")
        self.tab_all.addTab(self.tab_edges, "")
        self.horizontalLayout_4.addWidget(self.tab_all)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtWidgets.QToolBar(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolBar.sizePolicy().hasHeightForWidth())
        self.toolBar.setSizePolicy(sizePolicy)
        self.toolBar.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.toolBar.setMovable(True)
        self.toolBar.setAllowedAreas(QtCore.Qt.AllToolBarAreas)
        self.toolBar.setOrientation(QtCore.Qt.Horizontal)
        self.toolBar.setIconSize(QtCore.QSize(70, 40))
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionOpen = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/images/52.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionOpen.setIcon(icon)
        self.actionOpen.setObjectName("actionOpen")
        self.actionOptions = QtWidgets.QAction(MainWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/images/24x24/Application.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon1.addPixmap(QtGui.QPixmap(":/images/24x24/Application.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionOptions.setIcon(icon1)
        self.actionOptions.setObjectName("actionOptions")
        self.actionSave = QtWidgets.QAction(MainWindow)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/images/images/22.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSave.setIcon(icon2)
        self.actionSave.setObjectName("actionSave")
        self.actionComment = QtWidgets.QAction(MainWindow)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/images/24x24/Notes.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon3.addPixmap(QtGui.QPixmap(":/images/24x24/Notes.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionComment.setIcon(icon3)
        self.actionComment.setObjectName("actionComment")
        self.actionHelp = QtWidgets.QAction(MainWindow)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/images/24x24/Help book 3d.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionHelp.setIcon(icon4)
        self.actionHelp.setObjectName("actionHelp")
        self.actionEDI = QtWidgets.QAction(MainWindow)
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.actionEDI.setFont(font)
        self.actionEDI.setObjectName("actionEDI")
        self.actionCheck = QtWidgets.QAction(MainWindow)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/images/24x24/Red mark.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionCheck.setIcon(icon5)
        self.actionCheck.setObjectName("actionCheck")
        self.actionBT = QtWidgets.QAction(MainWindow)
        self.actionBT.setCheckable(False)
        self.actionBT.setChecked(False)
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.actionBT.setFont(font)
        self.actionBT.setObjectName("actionBT")
        self.actionGGA = QtWidgets.QAction(MainWindow)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.actionGGA.setFont(font)
        self.actionGGA.setObjectName("actionGGA")
        self.actionVTG = QtWidgets.QAction(MainWindow)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.actionVTG.setFont(font)
        self.actionVTG.setObjectName("actionVTG")
        self.actionNav_Reference = QtWidgets.QAction(MainWindow)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.actionNav_Reference.setFont(font)
        self.actionNav_Reference.setObjectName("actionNav_Reference")
        self.actionComp_Tracks = QtWidgets.QAction(MainWindow)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.actionComp_Tracks.setFont(font)
        self.actionComp_Tracks.setObjectName("actionComp_Tracks")
        self.actionON = QtWidgets.QAction(MainWindow)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.actionON.setFont(font)
        self.actionON.setObjectName("actionON")
        self.actionOFF = QtWidgets.QAction(MainWindow)
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.actionOFF.setFont(font)
        self.actionOFF.setObjectName("actionOFF")
        self.toolBar.addAction(self.actionOpen)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionSave)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionOptions)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionComment)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionCheck)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionEDI)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionNav_Reference)
        self.toolBar.addAction(self.actionBT)
        self.toolBar.addAction(self.actionGGA)
        self.toolBar.addAction(self.actionVTG)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionComp_Tracks)
        self.toolBar.addAction(self.actionON)
        self.toolBar.addAction(self.actionOFF)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionHelp)

        self.retranslateUi(MainWindow)
        self.tab_all.setCurrentIndex(0)
        self.tab_summary.setCurrentIndex(0)
        self.tab_mc.setCurrentIndex(0)
        self.tab_systest_2.setCurrentIndex(1)
        self.tab_compass_2.setCurrentIndex(2)
        self.tab_tempsal_2.setCurrentIndex(0)
        self.tab_mtb_2.setCurrentIndex(1)
        self.tab_bt_2.setCurrentIndex(0)
        self.tab_gps_2.setCurrentIndex(1)
        self.tab_depth_2.setCurrentIndex(1)
        self.tab_wt_2.setCurrentIndex(1)
        self.tab_extrap_2.setCurrentIndex(1)
        self.tab_edges_2.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.tab_summary.setTabText(self.tab_summary.indexOf(self.tab_summary_discharge), _translate("MainWindow", "Summary"))
        self.tab_summary.setTabText(self.tab_summary.indexOf(self.tab_summary_details), _translate("MainWindow", "Details"))
        self.tab_summary.setTabText(self.tab_summary.indexOf(self.tab_summary_premeasurement), _translate("MainWindow", "Premeasurement"))
        self.tab_summary.setTabText(self.tab_summary.indexOf(self.tab_summary_settings), _translate("MainWindow", "Settings"))
        self.tab_mc.setTabText(self.tab_mc.indexOf(self.tab_mc_messages), _translate("MainWindow", "Messages"))
        self.tab_mc.setTabText(self.tab_mc.indexOf(self.tab_mc_comments), _translate("MainWindow", "Comments"))
        self.tab_all.setTabText(self.tab_all.indexOf(self.tab_main), _translate("MainWindow", "Main"))
        self.tab_systest_2.setTabText(self.tab_systest_2.indexOf(self.tab_systest_2_results), _translate("MainWindow", "Results"))
        self.tab_systest_2.setTabText(self.tab_systest_2.indexOf(self.tab_systest_2_messages), _translate("MainWindow", "Messages"))
        self.tab_all.setTabText(self.tab_all.indexOf(self.tab_systest), _translate("MainWindow", "SysTest"))
        self.tab_compass_2.setTabText(self.tab_compass_2.indexOf(self.tab_compass_2_data), _translate("MainWindow", "Data"))
        self.tab_compass_2.setTabText(self.tab_compass_2.indexOf(self.tab_compass_2_cal), _translate("MainWindow", "Calibration / Evaluation"))
        self.tab_compass_2.setTabText(self.tab_compass_2.indexOf(self.tab_compass_2_messages), _translate("MainWindow", "Messages"))
        self.tab_all.setTabText(self.tab_all.indexOf(self.tab_compass), _translate("MainWindow", "Compass/P/R"))
        self.tab_tempsal_2.setTabText(self.tab_tempsal_2.indexOf(self.tab_tempsal_2_data), _translate("MainWindow", "Data"))
        self.tab_tempsal_2.setTabText(self.tab_tempsal_2.indexOf(self.tab_tempsal_2_messages), _translate("MainWindow", "Messages"))
        self.tab_all.setTabText(self.tab_all.indexOf(self.tab_tempsal), _translate("MainWindow", "Temp/Sal"))
        self.tab_mtb_2.setTabText(self.tab_mtb_2.indexOf(self.tab_mbt_2_data), _translate("MainWindow", "Data"))
        self.tab_mtb_2.setTabText(self.tab_mtb_2.indexOf(self.tab_mbt_2_messages), _translate("MainWindow", "Messages"))
        self.tab_all.setTabText(self.tab_all.indexOf(self.tab_mbt), _translate("MainWindow", "MovBedTst"))
        self.tab_bt_2.setTabText(self.tab_bt_2.indexOf(self.tab_bt_2_data), _translate("MainWindow", "Data"))
        self.tab_bt_2.setTabText(self.tab_bt_2.indexOf(self.tab_bt_2_messages), _translate("MainWindow", "Messages"))
        self.tab_all.setTabText(self.tab_all.indexOf(self.tab_bt), _translate("MainWindow", "BT"))
        self.tab_gps_2.setTabText(self.tab_gps_2.indexOf(self.tab_gps_2_data), _translate("MainWindow", "Data"))
        self.tab_gps_2.setTabText(self.tab_gps_2.indexOf(self.tab_gps_2_messages_2), _translate("MainWindow", "Messages"))
        self.tab_all.setTabText(self.tab_all.indexOf(self.tab_gps), _translate("MainWindow", "GPS"))
        self.tab_depth_2.setTabText(self.tab_depth_2.indexOf(self.tab_depth_2_data), _translate("MainWindow", "Data"))
        self.tab_depth_2.setTabText(self.tab_depth_2.indexOf(self.tab_gps_2_messages_3), _translate("MainWindow", "Messages"))
        self.tab_all.setTabText(self.tab_all.indexOf(self.tab_depth), _translate("MainWindow", "Depth"))
        self.tab_wt_2.setTabText(self.tab_wt_2.indexOf(self.tab_wt_2_data), _translate("MainWindow", "Data"))
        self.tab_wt_2.setTabText(self.tab_wt_2.indexOf(self.tab_wt_2_messages), _translate("MainWindow", "Messages"))
        self.tab_all.setTabText(self.tab_all.indexOf(self.tab_wt), _translate("MainWindow", "WT"))
        self.tab_extrap_2.setTabText(self.tab_extrap_2.indexOf(self.tab_extrap_2_data), _translate("MainWindow", "Data"))
        self.tab_extrap_2.setTabText(self.tab_extrap_2.indexOf(self.tab_wt_2_messages_2), _translate("MainWindow", "Messages"))
        self.tab_all.setTabText(self.tab_all.indexOf(self.tab_extrap), _translate("MainWindow", "Extrap"))
        self.tab_edges_2.setTabText(self.tab_edges_2.indexOf(self.tab_edges_2_data), _translate("MainWindow", "Data"))
        self.tab_edges_2.setTabText(self.tab_edges_2.indexOf(self.tab_wt_2_messages_3), _translate("MainWindow", "Messages"))
        self.tab_all.setTabText(self.tab_all.indexOf(self.tab_edges), _translate("MainWindow", "Edges"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.actionOpen.setText(_translate("MainWindow", "Open"))
        self.actionOpen.setToolTip(_translate("MainWindow", "Opens measurement data file(s)"))
        self.actionOptions.setText(_translate("MainWindow", "options"))
        self.actionOptions.setToolTip(_translate("MainWindow", "Optional Settings"))
        self.actionSave.setText(_translate("MainWindow", "Save"))
        self.actionComment.setText(_translate("MainWindow", "Comment"))
        self.actionHelp.setText(_translate("MainWindow", "Help"))
        self.actionEDI.setText(_translate("MainWindow", "EDI"))
        self.actionCheck.setText(_translate("MainWindow", "UncheckAll"))
        self.actionBT.setText(_translate("MainWindow", "BT"))
        self.actionBT.setToolTip(_translate("MainWindow", "BT"))
        self.actionGGA.setText(_translate("MainWindow", "GGA"))
        self.actionGGA.setToolTip(_translate("MainWindow", "GGA"))
        self.actionVTG.setText(_translate("MainWindow", "VTG"))
        self.actionVTG.setToolTip(_translate("MainWindow", "VTG"))
        self.actionNav_Reference.setText(_translate("MainWindow", "Nav Reference:"))
        self.actionNav_Reference.setToolTip(_translate("MainWindow", "Nav Reference:"))
        self.actionComp_Tracks.setText(_translate("MainWindow", "Comp Tracks:"))
        self.actionON.setText(_translate("MainWindow", "ON"))
        self.actionOFF.setText(_translate("MainWindow", "OFF"))

import dsm_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

