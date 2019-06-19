import sys
from PyQt5 import QtWidgets
from UI.RIVRS_Demo import RIVRS_Demo
from UI.QRev import QRev


class RIVRS_Controller:
    """This class serves as the central controller to allow two QMainWindows: RIVRS and QRev to work together.
    When the controller is run RIVRS, represented here as RIVRS_Demo, is opened first to allow the user to perform
    work in RIVRS. RIVRS will have the capability to load a measurement file and run the automatic processing of
    the transects using the Measurement class from QRev. Once the user has group the transects into the desired
    groups the user can click a button which will call the Show_QRev function in this class which will open QRev.
    Once all the processing is complete QRev will populate the processed_meas attribute and call Show_RIVRS
    to return control back to RIVRS and close QRev.

    Attributes
    ----------
    processed_meas: list
        List of dictionaries for each group containing 'group', 'start_serial_time', 'end_serial_time',
        and 'processed_discharge'
    RIVRS_Window: RIVRS
        Instance of the RIVRS QMainWindow
    QRev_Window: QRev
        Instance of the QRev QMainWindow
    """
    def __init__(self):
        # Initialize attributes
        self.processed_meas = None
        RIVRS_Window = None
        QRev_Window = None

    def Show_RIVRS(self):
        """Controls the display of the RIVRS GUI.
        """

        if self.processed_meas is None:
            # If processed_meas is None then the RIVRS GUI is opened as if it were run independent of the controller
            self.RIVRS_Window = RIVRS_Demo(caller=self)
            self.RIVRS_Window.show()

        else:
            # If processed_meas contains data this means that QRev has be run and a function in RIVRS, demoed here
            # with processed_data_table can be called and the processed_meas data passed to RIVRS
            self.RIVRS_Window.processed_data_table(data=self.processed_meas)
            self.RIVRS_Window.show()
            # The QRev GUI is closed automatically
            self.QRev_Window.close()

    def Show_QRev(self):
        """Controls the display of the QRev GUI.
        """
        self.QRev_Window = QRev(groupings=self.RIVRS_Window.groupings,
                                data=self.RIVRS_Window.meas,
                                caller=self)
        self.QRev_Window.show()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Controller = RIVRS_Controller()
    Controller.Show_RIVRS()
    sys.exit(app.exec_())
