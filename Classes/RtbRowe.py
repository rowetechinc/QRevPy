import os
import re
import logging
import numpy as np
import struct
from MiscLibs.common_functions import pol2cart, valid_number, nans
import crc16


class RtbRowe(object):
    """Class to read data from RTB files

    """

    # Prevent Magic Numbers
    HEADER_SIZE = 32                    # Header size in bytes
    CHECKSUM_SIZE = 4                   # Checksum size in bytes
    MAX_DATASETS = 20                   # Maximum number of datasets in an ensemble
    BYTES_IN_INT32 = 4                  # Bytes in Int32
    BYTES_IN_FLOAT = 4                  # Bytes in Float
    NUM_DATASET_HEADER_ELEMENTS = 6     # Number of elements in dataset header

    def __init__(self, file_name):
        """Constructor initializing instance variables.

        Parameters
        ----------
        file_name: str
            Full name including path of RTB file to be read
        """

        self.file_name = file_name
        self.Ens = None
        self.Anc = None
        self.Amp = None
        self.Corr = None
        self.Beam = None
        self.Instr = None
        self.Earth = None
        self.GdB = None
        self.GdE = None
        self.Rt = None
        self.Wt = None
        self.Bt = None
        self.Sys = None
        self.Gps = None
        self.Gps2 = None
        self.Surface = None
        self.AutoMode = None
        self.Nmea = None

        # Ensemble index to keep track of the number of ensembles found
        self.ens_index = 0

        self.rtb_read(file_name)

    def create_objects(self, n_ensembles, n_types, n_bins, max_surface_bins, n_velocities, wr2=False):
        """Create objects for instance variables.

        Parameters
        ----------
        n_ensembles: int
            Number of ensembles
        n_types: int
            Number of data types
        n_bins: int
            Number of bins or depth cells
        max_surface_bins: int
            Maximum number of surface cells
        n_velocities: int
            Number of velocities
        wr2: bool
            Whether WR2 processing of GPS data should be applied
        """

        self.Hdr = Hdr(n_ensembles, n_types)
        self.Inst = Inst(n_ensembles)
        self.Cfg = Cfg(n_ensembles)
        self.Sensor = Sensor(n_ensembles)
        self.Wt = Wt(n_bins, n_ensembles, n_velocities)
        self.Bt = Bt(n_ensembles, n_velocities)
        self.Gps = Gps(n_ensembles)
        self.Gps2 = Gps2(n_ensembles, wr2)
        self.Surface = Surface(n_ensembles, n_velocities, max_surface_bins)
        self.AutoMode = AutoMode(n_ensembles)
        self.Nmea = Nmea(n_ensembles)

    def rtb_read(self, fullname, wr2=False):
        """Reads the binary RTB file and assigns values to object instance variables.

        Parameters
        ----------
        fullname: str
            Full file name including path
        wr2: bool
            Determines if WR2 processing should be applied to GPS data
        """

        # RTB ensemble delimiter
        DELIMITER = b'\x80' * 16

        # Block size to read in data
        BLOCK_SIZE = 4096

        # Get the total file size to keep track of total bytes read and show progress
        file_size = os.path.getsize(fullname)
        bytes_read = 0

        # Create a buffer
        buff = bytes()

        # Assign default values
        n_velocities = 4
        max_surface_bins = 5

        # Check to ensure file exists
        if os.path.exists(fullname):
            file_info = os.path.getsize(fullname)

            with open(fullname, "rb") as f:
                data = f.read(BLOCK_SIZE)  # Read in data

                # Keep track of bytes read
                #bytes_read += BLOCK_SIZE
                #self.file_progress(bytes_read, file_size, fullname)

                # Verify data was found
                while data:
                    # Accumulate the buffer
                    buff += data

                    # Check for the delimiter
                    if DELIMITER in buff:
                        # If delimiter found, split at the delimiter to get the remaining buffer data
                        chunks = buff.split(DELIMITER)

                        # Put the remaining data back in the buffer
                        buff = chunks.pop()

                        # Take out the ens data
                        for chunk in chunks:
                            # Process the binary ensemble data
                            self.decode_ens(DELIMITER + chunk)

                    # Read the next batch of data
                    data = f.read(BLOCK_SIZE)

                    # Keep track of bytes read
                    bytes_read += BLOCK_SIZE
                    # self.file_progress(bytes_read, file_size, ens_file_path)
                    #self.file_progress(BLOCK_SIZE, file_size, fullname)

            # Process whatever is remaining in the buffer
            self.process_playback_ens(DELIMITER + buff)

    def decode_ens(self, ens_bytes: list, ens_index: int):
        """
        Atttempt to decode the ensemble.  This will verify the checksum passes.
        If the checksum is good, then decode the data.
        """

        # Verify the ENS data is good
        # This will check that all the data is there and the checksum is good
        if self.verify_ens_data(ens_bytes):
            # Decode the ens binary data
            logging.debug("Decoding binary data to ensemble: " + str(len(ens_bytes)))
            ens = self.decode_data_sets(ens_bytes, ens_index)

            # Increment the ensemble index
            self.ens_index += 1

    def verify_ens_data(self, ens_bytes: list, ens_start: int = 0):
        """
        Get the ensemble number and the ensemble size.  Verify
        we have all the ensemble bytes in the buffer by comparing aginst
        the ensemble size.  Then check the checksum and verify it is correct.
        :param ens_bytes: Ensemble binary data.
        :param ens_start: Start location in the ens_data
        :return True if the ensemble is good and checksum passes.
        """
        try:
            # Ensemble Length
            ens_len = len(ens_bytes)

            # Verify at least the minimum number of bytes are available to verify the ensemble
            if ens_len <= self.HEADER_SIZE + self.CHECKSUM_SIZE:
                return False

            # Check Ensemble number
            ens_num = struct.unpack("I", ens_bytes[ens_start + 16:ens_start + 20])

            # Check ensemble size
            payload_size = struct.unpack("I", ens_bytes[ens_start + 24:ens_start + 28])

            # Ensure the entire ensemble is in the buffer
            if ens_len >= ens_start + self.HEADER_SIZE + payload_size[0] + self.CHECKSUM_SIZE:

                # Check checksum
                checksum_loc = ens_start + self.HEADER_SIZE + payload_size[0]
                checksum = struct.unpack("I", ens_bytes[checksum_loc:checksum_loc + self.CHECKSUM_SIZE])

                # Calculate Checksum
                # Use only the payload for the checksum
                ens = ens_bytes[ens_start + self.HEADER_SIZE:ens_start + self.HEADER_SIZE + payload_size[0]]
                calc_checksum = crc16.crc16xmodem(ens)

                # Verify checksum
                if checksum[0] == calc_checksum:
                    logging.debug(ens_num[0])
                    return True
                else:
                    logging.warning("Ensemble fails checksum. {:#04x} {:#04x}".format(checksum[0], calc_checksum))
                    return False
            else:
                logging.warning("Incomplete ensemble.")
                return False

        except Exception as e:
            logging.error("Error verifying Ensemble.  " + str(e))
            return False

        return False

    def decode_data_sets(self, ens_bytes: list, ens_index: int, ensemble=None):
        """
        Decode the datasets to an ensemble.
        Use verify_ens_data if you are using this
        as a static method to verify the data is correct.
        :param ens_bytes: Ensemble binary data.  Decode the dataset.
        :param enx_index: Index to fill in the values.
        :return: Return the decoded ensemble.
        """
        packetPointer = self.HEADER_SIZE
        #type = 0
        #numElements = 0
        #elementMultiplier = 0
        #imag = 0
        #nameLen = 0
        #name = ""
        #dataSetSize = 0
        ens_len = len(ens_bytes)

        # Decode the ensemble datasets
        # Limit the number of attempts to look for new datasets
        for x in range(self.MAX_DATASETS):
            # Check if we are at the end of the payload
            if packetPointer >= ens_len - RtbRowe.CHECKSUM_SIZE - RtbRowe.HEADER_SIZE:
                break

            # Get the dataset info
            ds_type = RtbRowe.get_int32(packetPointer + (RtbRowe.BYTES_IN_INT32 * 0), RtbRowe.BYTES_IN_INT32, ens_bytes)
            num_elements = RtbRowe.get_int32(packetPointer + (RtbRowe.BYTES_IN_INT32 * 1), RtbRowe.BYTES_IN_INT32, ens_bytes)
            element_multiplier = RtbRowe.get_int32(packetPointer + (RtbRowe.BYTES_IN_INT32 * 2), RtbRowe.BYTES_IN_INT32, ens_bytes)
            image = RtbRowe.get_int32(packetPointer + (RtbRowe.BYTES_IN_INT32 * 3), RtbRowe.BYTES_IN_INT32, ens_bytes)
            name_len = RtbRowe.get_int32(packetPointer + (RtbRowe.BYTES_IN_INT32 * 4), RtbRowe.BYTES_IN_INT32, ens_bytes)
            name = str(ens_bytes[packetPointer + (RtbRowe.BYTES_IN_INT32 * 5):packetPointer + (RtbRowe.BYTES_IN_INT32 * 5) + 8], 'UTF-8')

            # Calculate the dataset size
            data_set_size = RtbRowe.get_data_set_size(ds_type, name_len, num_elements, element_multiplier)

            # Beam Velocity
            if "E000001" in name:
                logging.debug(name)
                bv = BeamVelocity(pd0_format=True)
                bv.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                          num_elements=num_elements,
                          element_multiplier=element_multiplier)
                ensemble.AddBeamVelocity(bv)

            # Instrument Velocity
            if "E000002" in name:
                logging.debug(name)
                iv = InstrVelocity(pd0_format=True)
                iv.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                          num_elements=num_elements,
                          element_multiplier=element_multiplier)
                ensemble.AddInstrumentVelocity(iv)

            # Earth Velocity
            if "E000003" in name:
                logging.debug(name)
                ev = EarthVelocity(pd0_format=True)
                ev.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                          num_elements=num_elements,
                          element_multiplier=element_multiplier)
                ensemble.AddEarthVelocity(ev)

            # Amplitude
            if "E000004" in name:
                logging.debug(name)
                amp = Amplitude(num_elements, element_multiplier)
                amp.decode(ens[packetPointer:packetPointer+data_set_size])
                ensemble.AddAmplitude(amp)

            # Correlation
            if "E000005" in name:
                logging.debug(name)
                corr = Correlation(num_elements, element_multiplier)
                corr.decode(ens_bytes[packetPointer:packetPointer+data_set_size])
                ensemble.AddCorrelation(corr)

            # Good Beam
            if "E000006" in name:
                logging.debug(name)
                gb = GoodBeam(num_elements, element_multiplier)
                gb.decode(ens_bytes[packetPointer:packetPointer+data_set_size])
                ensemble.AddGoodBeam(gb)

            # Good Earth
            if "E000007" in name:
                logging.debug(name)
                ge = GoodEarth(num_elements, element_multiplier)
                ge.decode(ens_bytes[packetPointer:packetPointer+data_set_size])
                ensemble.AddGoodEarth(ge)

            # Ensemble Data
            if "E000008" in name:
                logging.debug(name)
                ed = EnsembleData(num_elements, element_multiplier)
                ed.decode(ens_bytes[packetPointer:packetPointer+data_set_size])
                ensemble.AddEnsembleData(ed)

            # Ancillary Data
            if "E000009" in name:
                logging.debug(name)
                ad = AncillaryData(num_elements, element_multiplier)
                ad.decode(ens_bytes[packetPointer:packetPointer+data_set_size])
                ensemble.AddAncillaryData(ad)

            # Bottom Track
            if "E000010" in name:
                logging.debug(name)
                bt = BottomTrack(num_elements, element_multiplier)
                bt.decode(ens_bytes[packetPointer:packetPointer + data_set_size])
                ensemble.AddBottomTrack(bt)

            # NMEA data
            if "E000011" in name:
                logging.debug(name)
                nd = NmeaData(num_elements, element_multiplier)
                nd.decode(ens_bytes[packetPointer:packetPointer + data_set_size])
                ensemble.AddNmeaData(nd)

            # System Setup
            if "E000014" in name:
                logging.debug(name)
                ss = SystemSetup(num_elements, element_multiplier)
                ss.decode(ens_bytes[packetPointer:packetPointer + data_set_size])
                ensemble.AddSystemSetup(ss)

            # Range Tracking
            if "E000015" in name:
                logging.debug(name)
                rt = RangeTracking(num_elements, element_multiplier)
                rt.decode(ens_bytes[packetPointer:packetPointer + data_set_size])
                ensemble.AddRangeTracking(rt)

            # Move to the next dataset
            packetPointer += data_set_size

    @staticmethod
    def get_data_set_size(ds_type: int, name_len: int, num_elements: int, element_multiplier: int):
        """
        Get the dataset size.
        :param ds_type: Dataset type. (Int, float, ...)
        :param name_len: Length of the name.
        :param num_elements: Number of elements.
        :param element_multiplier: Element element multiplier.
        :return: Size of the dataset in bytes.
        """

        # Number of bytes in the data type
        datatype_size = 4
        if ds_type == 50:      # Byte Datatype
            datatype_size = 1
        elif ds_type == 20:    # Int Datatype
            datatype_size = 4
        elif ds_type == 10:    # Float Datatype
            datatype_size = 4

        return ((num_elements * element_multiplier) * datatype_size) + RtbRowe.get_base_data_size(name_len)

    @staticmethod
    def get_base_data_size(name_len: int):
        """
        Get the size of the header for a dataset.
        :param name_len: Length of the name.
        :return: Dataset header size in bytes.
        """
        return name_len + (RtbRowe.BYTES_IN_INT32 * (RtbRowe.NUM_DATASET_HEADER_ELEMENTS - 1))

    @staticmethod
    def get_int32(start: int, num_bytes: int, ens_bytes: list):
        """
        Convert the bytes given into an Int32.
        This will look in the ens given.
        :param start: Start location in the ens_bytes.
        :param num_bytes: Number of bytes in the int32.
        :param ens_bytes: Buffer containing the bytearray data.
        :return: Int32 of the data in the buffer.
        """
        try:
            return struct.unpack("i", ens_bytes[start:start + num_bytes])[0]
        except Exception as e:
            logging.error("Error creating a Int32 from bytes. " + str(e))
            return 0

    @staticmethod
    def get_float(start: int, num_bytes: int, ens: list):
        """
        Convert the bytes given into an int32.
        This will look in the ens given.
        :param start: Start location.
        :param num_bytes: Number of bytes in the float.
        :param ens: Buffer containing the bytearray data.
        :return: Float of the data in the buffer.
        """
        try:
            return struct.unpack("f", ens[start:start + num_bytes])[0]
        except Exception as e:
            logging.debug("Error creating a float from bytes. " + str(e))
            return 0.0


class BeamVelocity:
    """
    Beam Velocity.
    Velocity data in the Beam Coordinate Transform. (Raw Velocity Data)
    """
    def __init__(self, , pd0_format: bool = False):
        """
        Initialize the list of Beam Velocity.

        Also set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the velocity scale will be mm/s instead of m/s.
        RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.vel = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8):
        """
        Decode the ensemble data for the Beam velocity.

        If PD0 format is selected, then change the beam order and scale to match PD0.
        RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1

        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    self.vel[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 1000.0
                else:
                    if beam == 0:
                        self.vel[3][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 1000.0
                    elif beam == 1:
                        self.vel[2][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 1000.0
                    elif beam == 2:
                        self.vel[0][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 1000.0
                    elif beam == 3:
                        self.vel[1][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 1000.0

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_FLOAT


class InstrVelocity:
    """
    Instrument Velocity.
    Velocity data in the Instrument Coordinate Transform.
    """

    def __init__(self, pd0_format: bool = False):
        """
        Initialize the list of Instrument Velocity.

        Also set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the velocity scale will be mm/s instead of m/s.
        RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.vel = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8):
        """
        Decode the ensemble data for the Instrument velocity.

        If PD0 format is selected, then change the beam order and scale to match PD0.
        RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1

        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                self.vel[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
                packet_pointer += RtbRowe.BYTES_IN_FLOAT


class EarthVelocity:
    """
    Earth Velocity.
    Velocity data in the Earth Coordinate Transform.
    """

    def __init__(self, pd0_format: bool = False):
        """
        Initialize the list of Earth Velocity.

        Also set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the velocity scale will be mm/s instead of m/s.
        RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.vel = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8):
        """
        Decode the ensemble data for the Earth velocity.
        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                self.vel[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
                packet_pointer += RtbRowe.BYTES_IN_FLOAT
