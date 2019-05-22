from PyQt5 import QtWidgets
import Panels.batch as batch
import sys
from UI.MeasSplitter import MeasSplitter


class dsm_test_split(QtWidgets.QMainWindow, batch.Ui_mainWindow):
    def __init__(self, parent=None):
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

        self.summary = []

    def find_files(self):
        """Finds all files in the folder and subfolder matching the criteria and saves them to a list."""

        # Disable save button until list is created
        self.pb_save.setEnabled(False)

        # Get top level folder from user
        fullName = QtWidgets.QFileDialog.getOpenFileNames(
            self, self.tr('Open File'))[0]

        split = MeasSplitter(files_in=fullName[0],
                             source='TRDI')

        pairings = [[0,1],[1,2], [0,2]]

        processed_measurements = split.pass2qrev(pairings)
        print('Complete')


        # Enable save button
        self.pb_save.setEnabled(True)

app = QtWidgets.QApplication(sys.argv)
window = dsm_test_split()
window.show()
app.exec_()