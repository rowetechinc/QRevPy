import os
import scipy.io as sio
from PyQt5 import QtWidgets
from Classes.stickysettings import StickySettings as SSet


class OpenMeasurementDialog(QtWidgets.QDialog):
    """Dialog to allow users to select measurement files for processing.

    Attributes
    ----------
    settings: dict
        Dictionary used to store user defined settings.
    fullName: list
        Full name of files including path.
    fileName: list
        List of one or more fileNames to be processed.
    pathName: str
        Path to folder containing files.
    type: str
        Type of file (SonTek, TRDI, QRev).
    checked: bool
        Switch for TRDI files (True: load only checked, False: load all).
    """

    def __init__(self, parent=None):

        super(OpenMeasurementDialog, self).__init__(parent)

        # Create settings object which contains the default folder
        self.settings = SSet(parent.settingsFile)

        # Initialize parameters
        self.fullName = []
        self.fileName = []
        self.pathName = []
        self.type = ''
        self.checked = False
        self.get_files()

    def get_files(self):
        """Get filenames and pathname for file(s) to be processed

        Allows the user to select one *.mmt or one *_QRev.mat or one or more SonTek *.mat files for
        processing. The selected folder becomes the default folder for subsequent
        selectFile requests.
        """

        # Get the current folder setting.
        folder = self.default_folder()

        # Get the full names (path + file) of the selected files
        self.fullName = QtWidgets.QFileDialog.getOpenFileNames(
                    self, self.tr('Open File'), folder,
                    self.tr('All (*.mat *.mmt *.rmmt);;SonTek Matlab File (*.mat);;TRDI mmt File (*.mmt);;Rowe rmmt File (*.rmmt);;'
                            'QRev File (*_QRev.mat)'))[0]

        # Initialize parameters
        self.type = ''
        self.checked = False

        # Process fullName if selection was made
        if self.fullName:
            self.process_names()
        self.close()

    def process_names(self):
        """Parses fullnames into filenames and pathnames, sets default folder, determines the type of files selected,
        checks that the files selected are consistent with the type of files.
        """
        # Parse filenames and pathname from fullName
        if isinstance(self.fullName, str):
            self.pathName, self.fileName = os.path.split(self.fullName)
        else:
            self.fileName = []
            for file in self.fullName:
                self.pathName, fileTemp = os.path.split(file)
                self.fileName.append(fileTemp)

        # Update the folder setting
        self.settings.set('Folder', self.pathName)

        # Determine file type
        if len(self.fileName) == 1:
            file_name, file_extension = os.path.splitext(self.fileName[0])

            # TRDI file
            if file_extension == '.mmt':
                self.type = 'TRDI'
                checked_transect_dialog = QtWidgets.QMessageBox()
                checked_transect_dialog.setIcon(QtWidgets.QMessageBox.Question)
                checked_transect_dialog.setWindowTitle("Checked Transects?")
                checked_transect_dialog.setText(
                    "Do you want to load ONLY checked transects?")
                checked_transect_dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                checked_transect_dialog.setDefaultButton(QtWidgets.QMessageBox.No)
                checked_transect_dialog = checked_transect_dialog.exec()

                if checked_transect_dialog == QtWidgets.QMessageBox.Yes:
                    self.checked == True
            elif file_extension == '.rmmt':
                self.type = 'Rowe'
                checked_transect_dialog = QtWidgets.QMessageBox()
                checked_transect_dialog.setIcon(QtWidgets.QMessageBox.Question)
                checked_transect_dialog.setWindowTitle("Checked Transects?")
                checked_transect_dialog.setText(
                    "Do you want to load ONLY checked transects?")
                checked_transect_dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                checked_transect_dialog.setDefaultButton(QtWidgets.QMessageBox.No)
                checked_transect_dialog = checked_transect_dialog.exec()

                if checked_transect_dialog == QtWidgets.QMessageBox.Yes:
                    self.checked == True

            # SonTek, Nortek, or QRev file
            else:
                mat_data = sio.loadmat(self.fullName[0], struct_as_record=False, squeeze_me=True)
                if 'version' in mat_data:
                    self.type = 'QRev'
                elif hasattr(mat_data['System'], 'InstrumentModel'):
                    self.type = 'Nortek'
                else:
                    self.type = 'SonTek'

        else:
            # If multiple files are selected they must all be SonTek or Nortek files
            for name in self.fileName:
                file_name, file_extension = os.path.splitext(name)
                if file_extension == '.mmt':
                    self.popup_message("Selected files contain an mmt file. An mmt file must be loaded separately")
                    break
                elif file_extension == '.mat':
                    mat_data = sio.loadmat(self.fullName[0], struct_as_record=False, squeeze_me=True)
                    if 'version' in mat_data:
                        self.popup_message("Selected files contain a QRev file. A QRev file must be opened separately")
                        break
                    elif hasattr(mat_data['System'], 'InstrumentModel'):
                        self.type = 'Nortek'
                        break
                    else:
                        self.type = 'SonTek'
                        break


    def default_folder(self):
        """Returns default folder.

        Returns the folder stored in settings or if no folder is stored, then the current
        working folder is returned.
        """
        try:
            folder = self.settings.get('Folder')
            if not folder:
                folder = os.getcwd()
        except KeyError:
            self.settings.new('Folder', os.getcwd())
            folder = self.settings.get('Folder')
        return folder

    @staticmethod
    def popup_message(text):
        """Display a message box with messages specified in text.

        Parameters
        ----------
        text: str
            Message to be displayed.
        """
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(text)
        msg.setWindowTitle("Error")
        msg.exec_()
