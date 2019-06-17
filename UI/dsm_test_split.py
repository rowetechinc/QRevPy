from PyQt5 import QtWidgets
import Panels.batch as batch
import sys
from Classes.Measurement import Measurement


class dsm_test_split(QtWidgets.QMainWindow, batch.Ui_mainWindow):
    def __init__(self, parent=None, caller=None):
        """Initializes settings and connections.

        Parameters
        ----------
        parent
            Identifies parent GUI.
        """
        super(dsm_test_split, self).__init__(parent)
        self.setupUi(self)

        # Initialize variables

        self.pb_save.setEnabled(False)

        # Create connections for buttons
        self.pb_find.clicked.connect(self.find_files)
        if caller is not None:
            self.pb_save.clicked.connect(caller.Show_SecondWindow)

        self.summary = []

    def find_files(self):
        """Finds all files in the folder and subfolder matching the criteria and saves them to a list."""

        # Disable save button until list is created
        self.pb_save.setEnabled(False)

        # Get top level folder from user
        fullName = QtWidgets.QFileDialog.getOpenFileNames(
            self, self.tr('Open File'))[0]

        source = 'TRDI'
        if source == 'SonTek':
            # Create measurement object
            self.meas = Measurement(in_file=fullName, source='SonTek', proc_type='QRev')

        elif source == 'TRDI':
            # Create measurement object
            self.meas = Measurement(in_file=fullName[0], source='TRDI', proc_type='QRev')

        elif source == 'QRev':
            self.meas = Measurement(in_file=fullName[0], source='QRev')

        self.pairings = [[0,1],[1,2], [0,2]]
        self.pairings = [[0,1],[1,2], [0,2]]

        # processed_measurements = split.pass2qrev(pairings)
        # print('Complete')


        # Enable save button
        self.pb_save.setEnabled(True)
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = dsm_test_split()
    window.show()
    app.exec_()