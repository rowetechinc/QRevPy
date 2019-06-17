import sys
from PyQt5 import QtCore, QtWidgets
from UI.RIVRS_Demo import RIVRS_Demo
from UI.QRev import QRev

class RIVRS_Controller:

    def __init__(self):
        self.processed_meas = None

    def Show_RIVRS(self):

        if self.processed_meas is None:
            self.RIVRS_Window = RIVRS_Demo(caller=self)
            self.RIVRS_Window.show()
        # self.FirstWindow.pb_save.clicked.connect(self.Show_SecondWindow())
        else:
            self.RIVRS_Window.processed_data_table(data=self.processed_meas)
            self.RIVRS_Window.show()
            self.QRev_Window.close()

    def Show_QRev(self):
        self.QRev_Window = QRev(pairings=self.RIVRS_Window.pairings,
                                 data=self.RIVRS_Window.meas,
                                 caller=self)
        self.QRev_Window.show()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Controller = RIVRS_Controller()
    Controller.Show_RIVRS()
    sys.exit(app.exec_())