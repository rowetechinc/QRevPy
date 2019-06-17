from UI.QRev import QRev
from Classes.Measurement import Measurement
from PyQt5 import QtWidgets
import sys


class MeasSplitter(object):
    """Class provides an interface between QRev and another code that allows QRev to efficient split a measurement
    file into multiple measurements.

    When instantiated MeasSplitter will process the provided raw measurement data using the computational engine
    designed for QRev and provide the processed data in the meas attribute. The external program can then make use
    of the processed data.

    To use the pass2QRev function the external program must provide a list of pairings that group transect indices
    into individual measurements. The QRev GUI is then run and the user can review and process each group. When
    the user has completed processing a pairing (group) into a measurement and saves that measurement the next
    pairing (group) will be automatically loaded in the QRev GUI. When the last pairing (group) is loaded
    QRev will return a list of dictionaries to the attribute processed_measurements which represent the final
    processed discharge for each of the pairings (groups).

    Example of code for external program
    Assume:
    path_2_raw_measurement_file: is the full path to the mmt file, *QRev.mat file, or a list of paths to SonTek mat files
    source: is the type of file (TRDI, SonTek, QRev)
    pairings: is a list of lists of meas.transect indices that represent individual measurements
            Example pairings = [[0, 1], [2, 3, 4, 5], [8, 9]]

    import MeasSplitter
    split = MeasSplitter(files_in=path_2_raw_measurement_file,
                         source=type_of_measurement_file)

    split.meas will contain the initially processed measurement
    Once the pairing are identified a summary of processed measurements can be computed

    self.processed_measurements = split.pass2qrev(pairings)


    Attributes
    ----------
    meas: object
        Object of class Measurement

    """

    def __init__(self, files_in, source):

        if source == 'SonTek':
            # Create measurement object
            self.meas = Measurement(in_file=files_in, source='SonTek', proc_type='QRev')

        elif source == 'TRDI':
            # Create measurement object
            self.meas = Measurement(in_file=files_in, source='TRDI', proc_type='QRev')

        elif source == 'QRev':
            self.meas = Measurement(in_file=files_in, source='QRev')

        # self.qrev = QRev()

    def pass2qrev (self, pairings):
        """QRev GUI is initiated using the self.meas data and the pairings created externally

        Parameters
        ----------
        pairings: list
            pairings is a list of lists of meas.transect indices that represent individual measurements
            Example pairings = [[0, 1], [2, 3, 4, 5], [8, 9]]

        Returns
        -------
        processed_measurements: list
            List of dictionaries
                group: tuple
                start_serial_time: float
                end_serial_time: float
                processed_discharge: float
        """
        # dsm = self.qrev.split_initialization(pairings = pairings, data = self.meas)
        qrev = QRev()
        dsm = qrev.split_initialization(pairings=pairings, data=self.meas)
        processing_complete = app.exec_()
        if processing_complete:
            return self.qrev.processed_measurements
