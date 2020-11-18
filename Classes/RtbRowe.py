import os
import re
import logging
import numpy as np
import struct
import binascii
import math


class RtbRowe(object):
    """
    Class to read data from RTB files

    Single file to read in RTB data, then create an list of objects.  The lists will contain all the
    data from the file.

    This file was specifically created to work in QRevPy to decode RTI data and follow QRevPy's data format.
    """

    # Prevent Magic Numbers
    HEADER_SIZE = 32                    # Header size in bytes
    CHECKSUM_SIZE = 4                   # Checksum size in bytes
    MAX_DATASETS = 20                   # Maximum number of datasets in an ensemble
    BYTES_IN_INT32 = 4                  # Bytes in Int32
    BYTES_IN_FLOAT = 4                  # Bytes in Float
    NUM_DATASET_HEADER_ELEMENTS = 6     # Number of elements in dataset header
    BAD_VEL = 88.888                    # RTB Bad Velocity
    PD0_BAD_VEL = -32768                # PD0 Bad Velocity
    PD0_BAD_AMP = 255                   # PD0 Bad Amplitude

    def __init__(self, file_path: str, use_pd0_format: bool = False):
        """
        Constructor initializing instance variables.
        Set the use_pd0_format value if you want the values stored as a PD0 file.
        PD0 uses different scales for its values compared to RTB.

        :param file_path: Full Path of RTB file to be read
        :param use_pd0_format: Determine if the data should be decoded as RTB or PD0 scales.
        """

        # File path
        self.file_name = file_path
        self.use_pd0_format = use_pd0_format

        # Count the number of ensembles in the file to initialize the np.array
        self.num_ens, self.num_beams, self.num_bins = self.get_file_info(file_path=file_path)

        # List of all the ensemble data decoded
        self.Inst = Inst(num_ens=self.num_ens)
        self.Cfg = Cfg(num_ens=self.num_ens, pd0_format=use_pd0_format)
        self.Sensor = Sensor(pd0_format=use_pd0_format)
        self.Amp = Amplitude(pd0_format=use_pd0_format)
        self.Corr = Correlation(pd0_format=use_pd0_format)
        self.Wt = Wt(pd0_format=use_pd0_format,
                     num_ens=self.num_ens,
                     num_beams=self.num_beams,
                     num_bins=self.num_bins)
        self.InstrVel = InstrVelocity(pd0_format=use_pd0_format)
        self.EarthVel = EarthVelocity(pd0_format=use_pd0_format)
        self.GdB = GoodBeam(pd0_format=use_pd0_format)
        self.GdE = GoodEarth(pd0_format=use_pd0_format)
        self.Rt = RT(pd0_format=use_pd0_format)
        self.Bt = BT(num_ens=self.num_ens,
                     num_beams=self.num_beams,
                     pd0_format=use_pd0_format)
        self.Nmea = Nmea(pd0_format=use_pd0_format)
        self.Gage = Gage(pd0_format=use_pd0_format)
        self.Gps = []
        self.Gps2 = []
        self.Surface = Surface(num_ens=self.num_ens,
                               num_beams=self.num_beams,
                               max_surface_bins=0)          # NOT USED RIGHT NOW
        self.AutoMode = []
        self.River_BT = RiverBT(pd0_format=use_pd0_format)

        # Keep track of ensemble index
        # This is used only for 3 or 4 beam ensembles
        # Vertical beams are merged with 3 or 4 beam ensemble
        self.ens_index = 0

        # Read in the given file path
        self.rtb_read(file_path=file_path, use_pd0_format=self.use_pd0_format)

    @staticmethod
    def count_ensembles(file_path: str):
        """
        Get the file information like the number of ensembles in the file.
        """
        # RTB ensemble delimiter
        DELIMITER = b'\x80' * 16

        # Block size to read in data
        BLOCK_SIZE = 4096

        # Keep count of the number of ensembles found
        ens_count = 0

        # Search for the number of ensembles by looking for the delimiter
        # Check to ensure file exists
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read(BLOCK_SIZE)  # Read in data

                # Verify data was found
                while data:
                    # Check for the delimiter
                    if DELIMITER in data:
                        ens_count += 1

                    # Read the next batch of data
                    data = f.read(BLOCK_SIZE)

        return ens_count

    def get_file_info(self, file_path: str):
        """
        Get the file information like the number of ensembles,
        number of beams and number of bins.
        This only counts 3 or 4 beam ensembles.  Vertical beams
        will be merged with 4 beam ensembles.

        :param file_path File path to inspect.
        :return NumEnsembles, NumBeams, NumBins
        """
        # RTB ensemble delimiter
        DELIMITER = b'\x80' * 16

        # Block size to read in data
        BLOCK_SIZE = 4096

        # Create a buffer
        buff = bytes()

        # Keep count of the number of ensembles found
        ens_count = 0
        num_beams = 0
        num_bins = 0

        # Search for the number of ensembles by looking for the delimiter
        # Check to ensure file exists
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read(BLOCK_SIZE)  # Read in data

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
                            # Verify the ENS data is good
                            # This will check that all the data is there and the checksum is good
                            if self.verify_ens_data(DELIMITER + chunk):
                                # Get the ensemble info
                                bin_count, beams_count = self.get_ens_info(DELIMITER + chunk)

                                # Verify we have 3 or 4 beam data ensemble
                                # Vertical beam is not counted and is merged with 4 beam ensembles
                                if beams_count > 2:
                                    ens_count += 1

                                    # Set the largest beam and bin number
                                    num_beams = max(beams_count, num_beams)
                                    num_bins = max(bin_count, num_bins)

                    # Read the next batch of data
                    data = f.read(BLOCK_SIZE)

            # Process whatever is remaining in the buffer
            # Verify the ENS data is good
            # This will check that all the data is there and the checksum is good
            if self.verify_ens_data(DELIMITER + buff):
                # Get the ensemble info
                bin_count, beams_count = self.get_ens_info(DELIMITER + buff)

                # Verify we have 3 or 4 beam data ensemble
                # Vertical beam is not counted and is merged with 4 beam ensembles
                if beams_count > 2:
                    ens_count += 1

                    # Set the largest beam and bin number
                    num_beams = max(beams_count, num_beams)
                    num_bins = max(bin_count, num_bins)

        return ens_count, num_beams, num_bins

    def get_ens_info(self, ens_bytes: list):
        """
        Decode the datasets to an ensemble to get the general information about the ensemble.
        This includes the number of beams and bins.
        Use verify_ens_data if you are using this
        as a static method to verify the data is correct.
        :param ens_bytes: Ensemble binary data.  Decode the dataset.
        :return: Return number of beam and number of bins.
        """
        packetPointer = self.HEADER_SIZE
        ens_len = len(ens_bytes)

        num_elements = 0
        element_multiplier = 0

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

            # Beam velocity will contain all the information we need
            if "E000001" in name:
                # Return the number bins and number of beams
                return num_elements, element_multiplier

        return num_elements, element_multiplier

    def rtb_read(self, file_path: str, wr2: bool = False, use_pd0_format: bool = False):
        """
        Reads the binary RTB file and assigns values to object instance variables.
        :param file_path: Full file path
        :param wr2: Determines if WR2 processing should be applied to GPS data
        :param use_pd0_format: Determine if data should be RTB or PD0 format.  Convert values to PD0 values.
        """

        # RTB ensemble delimiter
        DELIMITER = b'\x80' * 16

        # Block size to read in data
        BLOCK_SIZE = 4096

        # Get the total file size to keep track of total bytes read and show progress
        file_size = os.path.getsize(file_path)
        bytes_read = 0

        # Create a buffer
        buff = bytes()

        # Assign default values
        n_velocities = 4
        max_surface_bins = 5

        # Check to ensure file exists
        if os.path.exists(file_path):
            file_info = os.path.getsize(file_path)

            with open(file_path, "rb") as f:
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
                            self.decode_ens(DELIMITER + chunk, use_pd0_format=use_pd0_format)

                    # Read the next batch of data
                    data = f.read(BLOCK_SIZE)

                    # Keep track of bytes read
                    bytes_read += BLOCK_SIZE
                    # self.file_progress(bytes_read, file_size, ens_file_path)
                    #self.file_progress(BLOCK_SIZE, file_size, fullname)

            # Process whatever is remaining in the buffer
            self.decode_ens(DELIMITER + buff, use_pd0_format=use_pd0_format)

    def decode_ens(self, ens_bytes: list, use_pd0_format: bool = False):
        """
        Attempt to decode the ensemble.  This will verify the checksum passes.
        If the checksum is good, then decode the data.
        When the data is decoded, automatically add it to list of ensembles.
        :param ens_bytes: Ensemble byte array to decode.
        :param use_pd0_format: Flag if the data should be decoded to PD0 format.
        :return
        """

        # Verify the ENS data is good
        # This will check that all the data is there and the checksum is good
        if self.verify_ens_data(ens_bytes):
            # Decode the ens binary data
            logging.debug("Decoding binary data to ensemble: " + str(len(ens_bytes)))

            # Decode the data
            self.decode_data_sets(ens_bytes, use_pd0_format=use_pd0_format)

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
                calc_checksum = binascii.crc_hqx(ens, 0)

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

    def decode_data_sets(self, ens_bytes: list, use_pd0_format: bool = False):
        """
        Decode the datasets to an ensemble.
        Use verify_ens_data if you are using this
        as a static method to verify the data is correct.
        :param ens_bytes: Ensemble binary data.  Decode the dataset.
        :param use_pd0_format: Flag to decode and convert data to PD0 format.
        :return: Return the decoded ensemble.
        """
        packetPointer = self.HEADER_SIZE
        ens_len = len(ens_bytes)

        # Flag if BT data found
        bt_data_found = False
        bt_adcp3_data_found = False
        ancillary_adcp3_found = False

        # Flag if this ensemble is vertical beam ensemble
        is_vert_ens = False

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

                # Test if this ensemble is a vertical beam
                if element_multiplier < 2:
                    is_vert_ens = True
                    # Add vertical beam ensemble
                else:
                    self.Wt.decode_vel(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                       ens_index=self.ens_index,
                                       num_elements=num_elements,
                                       element_multiplier=element_multiplier,
                                       name_len=name_len)

            # Instrument Velocity
            if "E000002" in name:
                logging.debug(name)
                self.InstrVel.decode(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                     num_elements=num_elements,
                                     element_multiplier=element_multiplier,
                                     name_len=name_len)

            # Earth Velocity
            if "E000003" in name:
                logging.debug(name)
                self.EarthVel.decode(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                     num_elements=num_elements,
                                     element_multiplier=element_multiplier,
                                     name_len=name_len)

            # Amplitude
            if "E000004" in name:
                logging.debug(name)

                # Check for vertical beam data
                if element_multiplier < 2:
                    is_vert_ens = True
                    # Add vertical beam ensemble
                else:
                    self.Wt.decode_rssi(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                        ens_index=self.ens_index,
                                        num_elements=num_elements,
                                        element_multiplier=element_multiplier,
                                        name_len=name_len)

            # Correlation
            if "E000005" in name:
                logging.debug(name)

                # Get code repeats for accurate conversion for PD0
                num_repeats = None
                if len(self.Cfg.wp_repeat_n) > self.ens_index-1 > 0 and not np.isnan(self.Cfg.wp_repeat_n[self.ens_index-1]):
                    num_repeats = self.Cfg.wp_repeat_n[self.ens_index-1]

                # Check for vertical beam data
                if element_multiplier < 2:
                    is_vert_ens = True
                    # Add vertical beam ensemble
                else:
                    self.Wt.decode_corr(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                        ens_index=self.ens_index,
                                        num_elements=num_elements,
                                        element_multiplier=element_multiplier,
                                        num_repeats=num_repeats,
                                        name_len=name_len)

            # Good Beam
            if "E000006" in name:
                logging.debug(name)

                # Get the number of pings used in the ensemble
                pings_per_ens = 1
                if len(self.Cfg.wp) > self.ens_index-1 > 0 and not np.isnan(self.Cfg.wp[self.ens_index-1]):
                    pings_per_ens = self.Cfg.wp[self.ens_index-1]

                # Check if vertical beam data
                if element_multiplier < 2:
                    is_vert_ens = True
                    # Add vertical beam ensemble
                else:
                    self.Wt.decode_pgb(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                       ens_index=self.ens_index,
                                       num_elements=num_elements,
                                       element_multiplier=element_multiplier,
                                       pings_per_ens=pings_per_ens,
                                       name_len=name_len)

            # Good Earth
            if "E000007" in name:
                logging.debug(name)

                # Get the number of pings used in the ensemble
                pings_per_ens = 1
                if len(self.Cfg.wp) > self.ens_index-1 > 0 and not np.isnan(self.Cfg.wp[self.ens_index-1]):
                    pings_per_ens = self.Cfg.wp[self.ens_index-1]

                self.GdE.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                num_elements=num_elements,
                                element_multiplier=element_multiplier,
                                pings_per_ens=pings_per_ens,
                                name_len=name_len)

            # Ensemble Data
            if "E000008" in name:
                logging.debug(name)
                # Check if the Cfg is already created from other dataset
                # This will be added to the list at the end of all decoding
                self.Cfg.decode_ensemble_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                              ens_index=self.ens_index,
                                              name_len=name_len)

                self.Inst.decode_ensemble_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                               ens_index=self.ens_index,
                                               name_len=name_len)

            # Ancillary Data
            if "E000009" in name:
                logging.debug(name)

                # Configuration data
                # Check if the Cfg is already created from other dataset
                # This will be added to the list at the end of all decoding
                self.Cfg.decode_ancillary_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                               ens_index=self.ens_index,
                                               name_len=name_len)

                # Sensor data
                # Check if the Sensor is already created from other dataset
                # This will be added to the list at the end of all decoding
                self.Sensor.decode_ancillary_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                  name_len=name_len)

                if num_elements > 19:
                    self.Sensor.decode_ancillary_adcp3_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                            name_len=name_len)
                    self.Cfg.decode_ancillary_adcp3_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                         name_len=name_len)
                    ancillary_adcp3_found = True

            # Bottom Track
            if "E000010" in name:
                logging.debug(name)
                # Populate Bottom Track data
                self.Bt.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                               ens_index=self.ens_index,
                               name_len=name_len)
                bt_data_found = True

                # Populate Config data
                self.Cfg.decode_bottom_track_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                  ens_index=self.ens_index,
                                                  name_len=name_len)

                # Populate Sensor data
                self.Sensor.decode_bottom_track_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                     name_len=name_len)

                # Check if ADCP 3 data is available
                # Number of elements.  74 for 4 Beam system, 59 for 3 beam, 29 for 1 beam
                if num_elements > 74:
                    self.Sensor.decode_bottom_track_adcp3_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                               name_len=name_len)
                    # Set flag that data found
                    bt_adcp3_data_found = True

            # NMEA data
            if "E000011" in name:
                logging.debug(name)
                self.Nmea.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                 name_len=name_len)

            # System Setup
            if "E000014" in name:
                logging.debug(name)
                # Configuration data
                # Check if the Cfg is already created from other dataset
                self.Cfg.decode_systemsetup_data(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                                 ens_index=self.ens_index,
                                                 name_len=name_len)

                self.Sensor.decode_systemsetup_data(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                                    name_len=name_len)

                self.Inst.decode_systemsetup_data(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                                  ens_index=self.ens_index,
                                                  name_len=name_len)

            # Range Tracking
            if "E000015" in name:
                logging.debug(name)
                self.Rt.decode(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                               name_len=name_len)

            if "E000016" in name:
                logging.debug(name)
                self.Gage.decode_data(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                      name_len=name_len)

            if "R000001" in name:
                logging.debug(name)
                self.River_BT.decode_data(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                          name_len=name_len)

            if "R000002" in name:
                logging.debug(name)
                #RiverTimeStamp

            if "R000003" in name:
                logging.debug(name)
                #RiverNmea

            if "R000004" in name:
                logging.debug(name)
                #RiverBThump

            if "R000005" in name:
                logging.debug(name)
                #RiverStationID

            if "R000006" in name:
                logging.debug(name)
                #RiverTransectID

            # Move to the next dataset
            packetPointer += data_set_size

        # Check if Bottom Track data was never found
        # If not fill values with NAN
        if not bt_data_found and self.Cfg:
            self.Sensor.empty_bt_init(num_beams=len(self.Inst.beams))

        if not bt_adcp3_data_found and self.Cfg:
            self.Sensor.empty_bt_adcp3_init(num_beams=len(self.Inst.beams))

        if not ancillary_adcp3_found:
            self.Sensor.empty_ancillary_adcp3_init()

        # Increment the ensemble index if not a vertical beam
        if not is_vert_ens:
            self.ens_index += 1

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
    def is_float_close(a, b, rel_tol=1e-06, abs_tol=0.0):
        """
        Check if the float values are the same.
        :param a: First float value
        :param b: Second float value
        :param rel_tol: Value within this
        :param abs_tol: Absolute value within this
        :return:
        """
        return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

    @staticmethod
    def is_bad_velocity(vel):
        """
        Check if the velocity given is good or bad.
        :param vel: Velocity value to check.
        :return: True if Bad Velocity.
        """
        if vel >= RtbRowe.BAD_VEL:
            return True
        if RtbRowe.is_float_close(vel, RtbRowe.BAD_VEL):
            return True
        if vel is None:
            return True

        return False

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

    @staticmethod
    def nans(num_ens: int):
        """
        Create a numpy array filled with NaN based on the number of
        ensembles given.
        @param num_ens: Number of ensembles
        """
        empty_arr = np.empty(num_ens, dtype=float)
        empty_arr.fill(np.nan)
        return empty_arr


class Wt:
    """
    Water Profile data.
    Beam Velocity.
    Velocity data in the Beam Coordinate Transform. (Raw Velocity Data)
    Correlation, Amplitude and Good Beam data for data quality.
    """
    def __init__(self, num_beams: int, num_bins: int, num_ens: int, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the velocity scale will be mm/s instead of m/s.
        RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1

        :param num_bins Number of bins/cells.
        :param num_beams Number of beams on the system.  Not including vertical beam
        :param num_ens Number of ensembles in file.
        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.corr = RtbRowe.nans([num_beams, num_bins, num_ens])            # Correlation in counts
        self.pergd = RtbRowe.nans([num_beams, num_bins, num_ens])           # Percent Good in percentage
        self.rssi = RtbRowe.nans([num_beams, num_bins, num_ens])            # RSSI/Amplitude in dB
        self.vel_mps = RtbRowe.nans([num_beams, num_bins, num_ens])         # Beam Velocity in m/s.
        self.pd0_format = pd0_format

    def decode_vel(self, ens_bytes: list, ens_index: int, num_elements: int, element_multiplier: int, name_len: int = 8):
        """
        Decode the ensemble data for the Beam velocity.

        Initialize the list of velocity data.  [beam][bin]

        If PD0 format is selected, then change the beam order and scale to match PD0.
        RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1

        RTB is m/s
        PD0 is mm/s
        RTB Bad Value is 88.888
        PD0 Bad Value is -32768

        :param ens_bytes: Byte array containing the ensemble data.
        :param ens_index: Ensemble Index.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    # Use the original value
                    vel[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Get the velocity data
                    pd0_vel = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

                    # Check for bad velocity and convert
                    if RtbRowe.is_bad_velocity(pd0_vel):
                        pd0_vel = RtbRowe.PD0_BAD_VEL
                    else:
                        # Convert from m/s to mm/s
                        pd0_vel = round(pd0_vel * 1000.0)

                    # Set the velocity based on the beam reassignment
                    if element_multiplier == 1:             # Vertical Beam
                        vel[0][bin_num] = pd0_vel
                    elif beam == 0:                         # RTB 0 - PD0 3
                        vel[3][bin_num] = pd0_vel
                    elif beam == 1:                         # RTB 1 - PD0 2
                        vel[2][bin_num] = pd0_vel
                    elif beam == 2:                         # RTB 2 - PD0 0
                        vel[0][bin_num] = pd0_vel
                    elif beam == 3:                         # RTB 3 - PD0 1
                        vel[1][bin_num] = pd0_vel

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_FLOAT

        # Reshape the data from [beam, bin] to [bin, beam]
        vel = np.reshape(vel, [num_elements, element_multiplier])
        # Add the data the numpy array [:num_beams, :num_bins, ens_index]
        self.vel_mps[:element_multiplier, :num_elements, ens_index] = vel.T

    def decode_rssi(self, ens_bytes: list, ens_index: int, num_elements: int, element_multiplier: int, name_len: int = 8):
        """
        Decode the ensemble data for the Amplitude data.

        Amplitude data which reports signal strength.
        Amplitude values range from 0 dB - 140 dB.
        Values below 25dB is considered noise.  The noise floor
        with systems with high EMI can be as a 40dB.

        Initialize the list of amplitude data.  [beam][bin]

        :param ens_bytes: Byte array containing the ensemble data.
        :param ens_index: Ensemble index to store the data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            amp = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            amp = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    amp[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Get the dB and convert to counts
                    pd0_amp = round(RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 2.0)

                    # Beam Reassignment
                    if element_multiplier == 1:                 # Vertical Beam
                        amp[beam][bin_num] = pd0_amp
                    elif beam == 0:                               # RTB 0 - PD0 3
                        amp[3][bin_num] = pd0_amp
                    elif beam == 1:                             # RTB 1 - PD0 2
                        amp[2][bin_num] = pd0_amp
                    elif beam == 2:                             # RTB 2 - PD0 0
                        amp[0][bin_num] = pd0_amp
                    elif beam == 3:                             # RTB 3 - PD0 1
                        amp[1][bin_num] = pd0_amp

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_FLOAT

        # Reshape the data from [beam, bin] to [bin, beam]
        amp = np.reshape(amp, [num_elements, element_multiplier])
        # Add the data the numpy array [:num_beams, :num_bins, ens_index]
        self.rssi[:element_multiplier, :num_elements, ens_index] = amp.T

    def decode_corr(self, ens_bytes: list, ens_index: int, num_elements: int, element_multiplier: int, name_len: int = 8, num_repeats: int = None):
        """
        Decode the ensemble data for the Correlation data.

        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the scale will change from percentage to counts.
        The value has to be converted from percentage to 0-255
        Scale 0%-100% to 0-255
        255 = 100%
        0   =   0%
        50% = 0.50 * 255 = 127.5 = 255/2

        RTB BEAM 0,1,2,3 = PD0 Corr 3,2,0,1

        Initialize the list of correlation data.  [beam][bin]

        :param ens_bytes: Byte array containing the ensemble data.
        :param ens_index: Ensemble index to store the data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        :param num_repeats: Only used when converting to PD0 format.  Accurately converts to counts.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            corr = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            corr = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    corr[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Verify a number of code repeats is given
                    if num_repeats and not np.isnan(num_repeats):
                        # Verify a good value for num_repeats
                        if num_repeats == 0:
                            num_repeats = 1

                        # Calculate code repeats used
                        repeats = (num_repeats - 1.0) / num_repeats
                        if repeats == 0.0:
                            repeats = 1.0

                        # Get the correlation percentage and convert to counts
                        pd0_corr = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 128.0
                        pd0_corr = round(pd0_corr / repeats)
                    else:
                        # If no repeats given, use this calculation
                        pd0_corr = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 255.0

                    # Beam Reassignment
                    if element_multiplier == 1:                 # Vertical Beam
                        corr[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 255.0
                    elif beam == 0:                               # RTB 0 - PD0 3
                        corr[3][bin_num] = pd0_corr
                    elif beam == 1:                             # RTB 1 - PD0 2
                        corr[2][bin_num] = pd0_corr
                    elif beam == 2:                             # RTB 2 - PD0 0
                        corr[0][bin_num] = pd0_corr
                    elif beam == 3:                             # RTB 3 - PD0 1
                        corr[1][bin_num] = pd0_corr

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_FLOAT

        # Reshape the data from [beam, bin] to [bin, beam]
        corr = np.reshape(corr, [num_elements, element_multiplier])
        # Add the data the numpy array [:num_beams, :num_bins, ens_index]
        self.corr[:element_multiplier, :num_elements, ens_index] = corr.T

    def decode_pgb(self, ens_bytes: list, ens_index: int, num_elements: int, element_multiplier: int, name_len: int = 8, pings_per_ens: int = 1):
        """
        Decode the ensemble data for the Good Beam Ping data.

        Good Beam Pings.  This give a number of pings
        that were used when averaging pings together.
        This will give a number of pings, so you will
        need to look at the settings to know the actual number
        of pings attempted.

        Initialize the list of Good Beam data.  [beam][bin]

        :param ens_bytes: Byte array containing the ensemble data.
        :param ens_index: Ensemble Index to store the data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        :param pings_per_ens: Only used when converting to PD0 format.  Number of pings in the ensemble
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            pings = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)
        else:
            pings = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    pings[beam][bin_num] = RtbRowe.get_int32(packet_pointer, RtbRowe.BYTES_IN_INT32, ens_bytes)
                else:
                    # Verify a good value for pings_per_ens
                    if pings_per_ens == 0:
                        pings_per_ens = 1

                    # Get the Good Beam number of good pings and convert to percentage
                    pd0_gb = round((RtbRowe.get_int32(packet_pointer, RtbRowe.BYTES_IN_INT32, ens_bytes) * 100) / pings_per_ens)

                    # Beam Reassignment
                    if element_multiplier == 1:                 # Vertical Beam
                        pings[beam][bin_num] = pd0_gb
                    elif beam == 0:                               # RTB 0 - PD0 3
                        pings[3][bin_num] = pd0_gb
                    elif beam == 1:                             # RTB 1 - PD0 2
                        pings[2][bin_num] = pd0_gb
                    elif beam == 2:                             # RTB 2 - PD0 0
                        pings[0][bin_num] = pd0_gb
                    elif beam == 3:                             # RTB 3 - PD0 1
                        pings[1][bin_num] = pd0_gb

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_INT32

        # Reshape the data from [beam, bin] to [bin, beam]
        pings = np.reshape(pings, [num_elements, element_multiplier])
        # Add the data the numpy array [:num_beams, :num_bins, ens_index]
        self.pergd[:element_multiplier, :num_elements, ens_index] = pings.T


class InstrVelocity:
    """
    Instrument Velocity.
    Velocity data in the Instrument Coordinate Transform.
    """

    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the velocity scale will be mm/s instead of m/s.
        RTB BEAM 0,1,2,3 = PD0 XYZ order 1,0,-2,3

        RTB is m/s
        PD0 is mm/s
        RTB Bad Value is 88.888
        PD0 Bad Value is -32768

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.vel = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8):
        """
        Decode the ensemble data for the Instrument velocity.

        Initialize the list of velocity data.  [beam][bin]

        If PD0 format is selected, then change the beam order and scale to match PD0.
        RTB BEAM 0,1,2,3 = PD0 XYZ order 1,0,-2,3

        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    vel[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Get the velocity data
                    pd0_vel = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

                    # Check for bad velocity and convert
                    if RtbRowe.is_bad_velocity(pd0_vel):
                        pd0_vel = RtbRowe.PD0_BAD_VEL
                    else:
                        # Convert from m/s to mm/s
                        pd0_vel = round(pd0_vel * 1000.0)

                    # Set the velocity based on the beam reassignment
                    if element_multiplier == 1:                     # Vertical Beam
                        vel[0][bin_num] = pd0_vel
                    elif beam == 0:                                 # RTB 0 - PD0 1
                        vel[1][bin_num] = pd0_vel
                    elif beam == 1:                                 # RTB 1 - PD0 0
                        vel[0][bin_num] = pd0_vel
                    elif beam == 2:                                 # RTB 2 - PD0 -2
                        if pd0_vel != RtbRowe.PD0_BAD_VEL:
                            vel[2][bin_num] = pd0_vel * -1.0
                        else:
                            vel[2][bin_num] = pd0_vel
                    elif beam == 3:                                 # RTB 3 - PD0 3
                        vel[3][bin_num] = pd0_vel

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_FLOAT

        # Add the data to the lsit
        self.vel.append(vel)


class EarthVelocity:
    """
    Earth Velocity.
    Velocity data in the Earth Coordinate Transform.
    """

    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the velocity scale will be mm/s instead of m/s.
        RTB BEAM 0,1,2,3 = PD0 ENU order 0,1,2,3

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.vel = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8):
        """
        Decode the ensemble data for the Earth velocity.

        Initialize the list of velocity data.  [beam][bin]

        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    vel[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Get the velocity data
                    pd0_vel = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

                    # Check for bad velocity and convert
                    if RtbRowe.is_bad_velocity(pd0_vel):
                        pd0_vel = RtbRowe.PD0_BAD_VEL
                    else:
                        # Convert from m/s to mm/s
                        pd0_vel = round(pd0_vel * 1000.0)

                    # Set the values
                    # No reassignment needed
                    vel[beam][bin_num] = pd0_vel

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_FLOAT

        # Add the data to the list
        self.vel.append(vel)


class Amplitude:
    """
    Amplitude.
    Amplitude data which reports signal strength.
    Amplitude values range from 0 dB - 140 dB.
    Values below 25dB is considered noise.  The noise floor
    with systems with high EMI can be as a 40dB.
    """
    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the scale will change from dB to counts. 0.5 dB per Count.
        RTB BEAM 0,1,2,3 = PD0 Amp 3,2,0,1

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.amp = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8):
        """
        Decode the ensemble data for the Amplitude data.

        Initialize the list of amplitude data.  [beam][bin]

        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            amp = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            amp = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    amp[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Get the dB and convert to counts
                    pd0_amp = round(RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 2.0)

                    # Beam Reassignment
                    if element_multiplier == 1:                 # Vertical Beam
                        amp[beam][bin_num] = pd0_amp
                    elif beam == 0:                               # RTB 0 - PD0 3
                        amp[3][bin_num] = pd0_amp
                    elif beam == 1:                             # RTB 1 - PD0 2
                        amp[2][bin_num] = pd0_amp
                    elif beam == 2:                             # RTB 2 - PD0 0
                        amp[0][bin_num] = pd0_amp
                    elif beam == 3:                             # RTB 3 - PD0 1
                        amp[1][bin_num] = pd0_amp

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_FLOAT

        # Add data to the list
        self.amp.append(amp)


class Correlation:
    """
    Correlation data which reports data quality.
    Value is reported as a percentage 0% - 100%.
    Values below 25% are considered bad or noise.

    If using PD0, values are between 0-255 counts.
    """
    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the scale will change from percentage to counts.
        The value has to be converted from percentage to 0-255
        Scale 0%-100% to 0-255
        255 = 100%
        0   =   0%
        50% = 0.50 * 255 = 127.5 = 255/2

        RTB BEAM 0,1,2,3 = PD0 Corr 3,2,0,1

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.corr = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8, num_repeats: int = None):
        """
        Decode the ensemble data for the Correlation data.

        Initialize the list of correlation data.  [beam][bin]

        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        :param num_repeats: Only used when converting to PD0 format.  Accurately converts to counts.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            corr = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            corr = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    corr[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Verify a number of code repeats is given
                    if num_repeats:
                        # Verify a good value for num_repeats
                        if num_repeats == 0:
                            num_repeats = 1

                        # Calculate code repeats used
                        repeats = (num_repeats - 1.0) / num_repeats
                        if repeats == 0.0:
                            repeats = 1.0

                        # Get the correlation percentage and convert to counts
                        pd0_corr = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 128.0
                        pd0_corr = round(pd0_corr / repeats)
                    else:
                        # If no repeats given, use this calculation
                        pd0_corr = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 255.0

                    # Beam Reassignment
                    if element_multiplier == 1:                 # Vertical Beam
                        corr[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 255.0
                    elif beam == 0:                               # RTB 0 - PD0 3
                        corr[3][bin_num] = pd0_corr
                    elif beam == 1:                             # RTB 1 - PD0 2
                        corr[2][bin_num] = pd0_corr
                    elif beam == 2:                             # RTB 2 - PD0 0
                        corr[0][bin_num] = pd0_corr
                    elif beam == 3:                             # RTB 3 - PD0 1
                        corr[1][bin_num] = pd0_corr

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_FLOAT

        # Add data to the list
        self.corr.append(corr)


class GoodBeam:
    """
    Good Beam Pings.  This give a number of pings
    that were used when averaging pings together.
    This will give a number of pings, so you will
    need to look at the settings to know the actual number
    of pings attempted.

    If using PD0, values are in percentage.
    """

    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the scale will change from the number of pings to percentage good.

        RTB GoodBeam 0,1,2,3 = PD0 GoodBeam 3,2,0,1

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.pings = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8, pings_per_ens: int = 1):
        """
        Decode the ensemble data for the Good Beam Ping data.

        Initialize the list of Good Beam data.  [beam][bin]

        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        :param pings_per_ens: Only used when converting to PD0 format.  Number of pings in the ensemble
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            pings = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)
        else:
            pings = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    pings[beam][bin_num] = RtbRowe.get_int32(packet_pointer, RtbRowe.BYTES_IN_INT32, ens_bytes)
                else:
                    # Verify a good value for pings_per_ens
                    if pings_per_ens == 0:
                        pings_per_ens = 1

                    # Get the Good Beam number of good pings and convert to percentage
                    pd0_gb = round((RtbRowe.get_int32(packet_pointer, RtbRowe.BYTES_IN_INT32, ens_bytes) * 100) / pings_per_ens)

                    # Beam Reassignment
                    if element_multiplier == 1:                 # Vertical Beam
                        pings[beam][bin_num] = pd0_gb
                    elif beam == 0:                               # RTB 0 - PD0 3
                        pings[3][bin_num] = pd0_gb
                    elif beam == 1:                             # RTB 1 - PD0 2
                        pings[2][bin_num] = pd0_gb
                    elif beam == 2:                             # RTB 2 - PD0 0
                        pings[0][bin_num] = pd0_gb
                    elif beam == 3:                             # RTB 3 - PD0 1
                        pings[1][bin_num] = pd0_gb

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_INT32

        # Add data to the list
        self.pings.append(pings)


class GoodEarth:
    """
    Good Earth Pings.  This give a number of pings
    that were used when averaging pings together.
    This will give a number of pings, so you will
    need to look at the settings to know the actual number
    of pings attempted.

    If using PD0, values are in percentage.
    """

    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the scale will change from the number of pings to percentage good.

        RTB GoodEarth 0,1,2,3 = PD0 GoodEarth 0,1,2,3

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.pings = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8, pings_per_ens: int = 1):
        """
        Decode the ensemble data for the Good Earth Ping data.

        Initialize the list of Good Beam data.  [beam][bin]

        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        :param pings_per_ens: Only used when converting to PD0 format.  Number of pings in the ensemble
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            pings = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)
        else:
            pings = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    pings[beam][bin_num] = RtbRowe.get_int32(packet_pointer, RtbRowe.BYTES_IN_INT32, ens_bytes)
                else:
                    # Verify a good value for pings_per_ens
                    if pings_per_ens == 0:
                        pings_per_ens = 1

                    # Get the Good Earth number of good pings and convert to percentage
                    # No reassignment needed
                    pings[beam][bin_num] = round((RtbRowe.get_int32(packet_pointer, RtbRowe.BYTES_IN_INT32, ens_bytes) * 100) / pings_per_ens)

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_INT32

        # Add data to the list
        self.pings.append(pings)


class Inst:
    """
    Instrument specific values.
    """
    def __init__(self, num_ens: int):
        """
        Initialize the values.
        """
        self.firm_major = RtbRowe.nans(num_ens)                 # Firmware Major Number
        self.firm_minor = RtbRowe.nans(num_ens)                 # Firmware Minor Number
        self.firm_rev = RtbRowe.nans(num_ens)                   # Firmware Revision
        self.firm_ver = RtbRowe.nans(num_ens)                   # Firmware version as a string
        self.beam_ang = RtbRowe.nans(num_ens)                   # Beam Angle in degrees
        self.beams = RtbRowe.nans(num_ens)                      # Number of beams used in velocity measurement
        self.freq = RtbRowe.nans(num_ens)                       # System frequency in Khz

    def decode_ensemble_data(self, ens_bytes: list, ens_index: int, name_len: int = 8):
        """
        Decode the ensemble data for the Instrument data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param ens_index: Ensemble index.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.beams[ens_index] = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 2, RtbRowe.BYTES_IN_INT32, ens_bytes)

        firm_rev = struct.unpack("B", ens_bytes[packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 0:packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 1])[0]
        firm_minor = struct.unpack("B", ens_bytes[packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 1:packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 2])[0]
        firm_major = struct.unpack("B", ens_bytes[packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 2:packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 3])[0]

        self.firm_rev[ens_index] = firm_rev
        self.firm_minor[ens_index] = firm_minor
        self.firm_major[ens_index] = firm_major
        self.firm_ver[ens_index] = round(firm_minor + (firm_rev/100.0), 2)

        # Determine the beam angle based on the subsystem type
        ss_code = str(ens_bytes[packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 3:packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 4], "UTF-8")
        if ss_code == "A" or ss_code == "B" or ss_code == "C":
            self.beam_ang[ens_index] = 0
        else:
            self.beam_ang[ens_index] = 20

    def decode_systemsetup_data(self, ens_bytes: list, ens_index: int, name_len: int = 8):
        """
        Decode the system setup data for the Configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param ens_index: Ensemble Index.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Get the frequency and convert from Hz to kHz
        freq = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

        freq_khz = np.nan
        if 60 > freq / 1000 > 80:
            freq_khz = 75
        elif 130 > freq / 1000 > 160:
            freq_khz = 150
        elif 200 > freq / 100 > 400:
            freq_khz = 300
        elif 400 > freq / 100 > 800:
            freq_khz = 600
        elif 1000 > freq / 100 > 1300:
            freq_khz = 1200
        elif 1800 > freq / 100 > 2500:
            freq_khz = 2400
        else:
            freq_khz = np.nan

        # Set the value
        self.freq[ens_index] = freq_khz


class Cfg:
    """
    System configuration data is all the data that describes the ADCP configuration and date and time.
    This includes the bin size, blank and number of bins, the ensemble number, date and time.
    """

    def __init__(self, num_ens: int, pd0_format: bool = False):
        """
        Initialize all the values
        Set the flag if using PD0 format data.  This will change the year from 2000+ date to year-2000

        :param num_ens: Number of ensembles.
        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.pd0_format = pd0_format

        self.ens_num = RtbRowe.nans(num_ens)                    # Ensemble number
        #self.num_bins = RtbRowe.nans(num_ens)                  # Replaced with wn Number of bins
        self.desired_ping_count = RtbRowe.nans(num_ens)         # Avg Ping Count configured in seconds
        #self.actual_ping_count = RtbRowe.nans(num_ens)         # Replaced with wp. Avg Ping Count actually output in seconds
        self.serial_num = RtbRowe.nans(num_ens)                 # Serial Number

        self.subsystem_code = RtbRowe.nans(num_ens)             # Subsystem Code (Identifier of frequency and orientation)
        self.subsystem_config = RtbRowe.nans(num_ens)           # Subsystem Config.  System allows multiple configures of the same frequency.  This identifies each configuration
        self.status = RtbRowe.nans(num_ens)                     # Status code
        self.year = RtbRowe.nans(num_ens)                       # Year
        self.month = RtbRowe.nans(num_ens)                      # Month
        self.day = RtbRowe.nans(num_ens)                        # Day
        self.hour = RtbRowe.nans(num_ens)                       # Hour
        self.minute = RtbRowe.nans(num_ens)                     # Minute
        self.second = RtbRowe.nans(num_ens)                     # Second
        self.hsec = RtbRowe.nans(num_ens)                       # Hundredth Second

        # ADCP 3 values
        self.current_system = RtbRowe.nans(num_ens)
        self.status_2 = RtbRowe.nans(num_ens)
        self.burst_index = RtbRowe.nans(num_ens)

        self.first_ping_time = RtbRowe.nans(num_ens)          # First Ping Time in seconds.
        self.last_ping_time = RtbRowe.nans(num_ens)           # Last Ping Time in seconds. (If averaging pings, this will be the last ping)
        self.salinity = RtbRowe.nans(num_ens)                 # Water Salinity set by the user in PPT
        self.speed_of_sound = RtbRowe.nans(num_ens)           # Speed of Sound in m/s.

        self.bt_first_ping_time = RtbRowe.nans(num_ens)
        self.bt_last_ping_time = RtbRowe.nans(num_ens)
        self.bt_speed_of_sound = RtbRowe.nans(num_ens)
        self.bt_status = RtbRowe.nans(num_ens)
        self.bt_num_beams = RtbRowe.nans(num_ens)
        self.bt_actual_ping_count = RtbRowe.nans(num_ens)

        self.bt_samples_per_second = RtbRowe.nans(num_ens)    # Bottom Track Samples Per Second
        self.bt_system_freq_hz = RtbRowe.nans(num_ens)        # Bottom Track System Frequency (Hz)
        self.bt_cpce = RtbRowe.nans(num_ens)                  # Bottom Track Carrier cycles per Code Elements
        self.bt_nce = RtbRowe.nans(num_ens)                   # Bottom Track Number of Code Elements contained in a lag
        self.bt_repeat_n = RtbRowe.nans(num_ens)              # Bottom Track Number of times the NCE is repeated in the transmit signal
        self.wp_samples_per_second = RtbRowe.nans(num_ens)    # Water Profile Samples per Second
        #self.wp_system_freq_hz = []        # Water Profile System Frequency (Hz)
        self.wp_cpce = RtbRowe.nans(num_ens)                  # Water Profile Carrier cycles per Code Elements
        self.wp_nce = RtbRowe.nans(num_ens)                   # Water Profile Number of Code Elements contained in a lag
        self.wp_repeat_n = RtbRowe.nans(num_ens)              # Water Profile Number of times the NCE is repeated in the transmit signal
        self.wp_lag_samples = RtbRowe.nans(num_ens)           # Water Profile Lag Samples
        self.bt_broadband = RtbRowe.nans(num_ens)             # Bottom Track Broadband
        self.bt_lag_length = RtbRowe.nans(num_ens)            # Bottom Track Pulse to Pulse Lag (m)
        self.bt_narrowband = RtbRowe.nans(num_ens)            # Bottom Track Long Range Switch Depth (m)
        self.bt_beam_mux = RtbRowe.nans(num_ens)              # Bottom Track Beam Multiplex
        self.wp_broadband = RtbRowe.nans(num_ens)             # Water Profile Mode
        self.lag_cm = RtbRowe.nans(num_ens)                   # Water Profile Lag Length
        self.lag_near_bottom = RtbRowe.nans(num_ens)          # Water Profile Lag Near Bottom
        self.wp_transmit_bandwidth = RtbRowe.nans(num_ens)    # Water Profile Transmit Bandwidth
        self.wp_receive_bandwidth = RtbRowe.nans(num_ens)     # Water Profile Receive Bandwidth
        self.wp_beam_mux = RtbRowe.nans(num_ens)              # WP Beam Mux

        self.ba = RtbRowe.nans(num_ens)                         # Bottom Track Amplitude Threshold
        self.bc = RtbRowe.nans(num_ens)                         # Bottom Track Correlation Threshold
        self.be_mmps = RtbRowe.nans(num_ens)                    # Bottom Track Error Velocity Threshold
        self.bg = RtbRowe.nans(num_ens)                         # Bottom Track Percent Good Threshold
        self.bm = RtbRowe.nans(num_ens)                         # Bottom Track Mode
        self.bp = RtbRowe.nans(num_ens)                         # Bottom Track Number of Pings
        self.bx_dm = RtbRowe.nans(num_ens)                      # Maximum Tracking depth in decimeters
        self.code_reps = RtbRowe.nans(num_ens)                  # Number of code repetitions
        self.coord_sys = [''] * num_ens                         # Coordinate System
        self.cpu_ser_no = RtbRowe.nans([num_ens, 8])            # CPU Serial Number
        self.cq = RtbRowe.nans(num_ens)                         # Transmit Power
        self.cx = RtbRowe.nans(num_ens)                         # Low Latency Trigger
        self.dist_bin1_cm = RtbRowe.nans(num_ens)               # * Distance to center of bin 1 from transducer
        self.ea_deg = RtbRowe.nans(num_ens)                     # Heading alignment
        self.eb_deg = RtbRowe.nans(num_ens)                     # Heading bias
        self.sensor_avail = [''] * num_ens                      # Sensor availability code
        self.ex = [''] * num_ens                                # Coordinate transformation codes
        self.ez = [''] * num_ens                                # Sensor codes
        self.head_src = [''] * num_ens                          # Heading sources
        self.lag_cm = RtbRowe.nans(num_ens)                     # * Lag Length in centimeter
        self.map_bins = [''] * num_ens                          # Bin Mapping
        self.n_beams = RtbRowe.nans(num_ens)                    # * Number of velocity beams
        self.pitch_src = [''] * num_ens                         # Source of pitch data
        self.ref_lay_end_cell = RtbRowe.nans(num_ens)           # Reference Layer end cell
        self.ref_lay_str_cell = RtbRowe.nans(num_ens)           # Reference Layer start cell
        self.roll_src = [''] * num_ens                          # Source of roll data
        self.sal_src = [''] * num_ens                           # Salinity Source
        self.wm = RtbRowe.nans(num_ens)                         # Water Mode
        self.sos_src = [''] * num_ens                           # Speed of Sound source
        self.temp_src = [''] * num_ens                          # Temperature Source
        self.tp_sec = RtbRowe.nans(num_ens)                     # * Time between Pings
        self.use_3beam = [''] * num_ens                         # Setting to use 3-Beam solution or not
        self.use_pr = [''] * num_ens                            # Setting to use pitch and roll or not
        self.wa = RtbRowe.nans(num_ens)                         # Water Track amplitude threshold
        self.wb = RtbRowe.nans(num_ens)                         # Water Track bandwidth threshold
        self.wc = RtbRowe.nans(num_ens)                         # Water Track correlation threshold
        self.we_mmps = RtbRowe.nans(num_ens)                    # Water Track error velocity threshold
        self.wf_cm = RtbRowe.nans(num_ens)                      # Blank after Transmit in cm
        self.wg_per = RtbRowe.nans(num_ens)                     # Water Track percent good threshold
        self.wj = RtbRowe.nans(num_ens)                         # Receiver Gain setting
        self.wn = RtbRowe.nans(num_ens)                         # * Number of depth cells (bins)
        self.wp = RtbRowe.nans(num_ens)                         # * Number of water pings
        self.ws_cm = RtbRowe.nans(num_ens)                      # * Bin size in cm
        self.xdcr_dep_srs = [''] * num_ens                      # Salinity Source
        self.xmit_pulse_cm = RtbRowe.nans(num_ens)              # Transmit Pulse length
        self.lag_near_bottom = RtbRowe.nans(num_ens)            # Lag near bottom setting

    def decode_ensemble_data(self, ens_bytes: list, ens_index: int, name_len: int = 8):
        """
        Decode the ensemble data for the configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param ens_index: Ensemble index to store the data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.ens_num[ens_index] = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 0, RtbRowe.BYTES_IN_INT32, ens_bytes)
        self.wn[ens_index] = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 1, RtbRowe.BYTES_IN_INT32, ens_bytes)
        self.n_beams[ens_index] = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 2, RtbRowe.BYTES_IN_INT32, ens_bytes)
        self.desired_ping_count[ens_index] = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 3, RtbRowe.BYTES_IN_INT32, ens_bytes)
        self.wp[ens_index] = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 4, RtbRowe.BYTES_IN_INT32, ens_bytes)
        self.status[ens_index] = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 5, RtbRowe.BYTES_IN_INT32, ens_bytes)
        #self.year.append(RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 6, RtbRowe.BYTES_IN_INT32, ens_bytes))
        self.month[ens_index] = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 7, RtbRowe.BYTES_IN_INT32, ens_bytes)
        self.day[ens_index] = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 8, RtbRowe.BYTES_IN_INT32, ens_bytes)
        self.hour[ens_index] = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 9, RtbRowe.BYTES_IN_INT32, ens_bytes)
        self.minute[ens_index] = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 10, RtbRowe.BYTES_IN_INT32, ens_bytes)
        self.second[ens_index] = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 11, RtbRowe.BYTES_IN_INT32, ens_bytes)
        self.hsec[ens_index] = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 12, RtbRowe.BYTES_IN_INT32, ens_bytes)

        self.serial_num[ens_index] = str(ens_bytes[packet_pointer + RtbRowe.BYTES_IN_INT32 * 13:packet_pointer + RtbRowe.BYTES_IN_INT32 * 21], "UTF-8")
        self.subsystem_code[ens_index] = str(ens_bytes[packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 3:packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 4], "UTF-8")
        self.subsystem_config[ens_index] = struct.unpack("B", ens_bytes[packet_pointer + RtbRowe.BYTES_IN_INT32 * 22 + 3:packet_pointer + RtbRowe.BYTES_IN_INT32 * 22 + 4])[0]

        if self.pd0_format:
            year = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 6, RtbRowe.BYTES_IN_INT32, ens_bytes)
            self.year[ens_index] = year - 2000
        else:
            self.year[ens_index] = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 6, RtbRowe.BYTES_IN_INT32, ens_bytes)

    def decode_ancillary_data(self, ens_bytes: list, ens_index: int, name_len: int = 8):
        """
        Decode the ancillary data for the Configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param ens_index: Ensemble index to store the data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.dist_bin1_cm[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 0, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 100.0
        self.ws_cm[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 100.0
        first_ping_time = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        last_ping_time = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

        self.first_ping_time[ens_index] = first_ping_time
        self.last_ping_time[ens_index] = last_ping_time
        self.tp_sec[ens_index] = last_ping_time - first_ping_time

        if self.pd0_format:
            salinity = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            sos = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            self.salinity[ens_index] = round(salinity)
            self.speed_of_sound[ens_index] = round(sos)
        else:
            self.salinity[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            self.speed_of_sound[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

    def decode_ancillary_adcp3_data(self, ens_bytes: list, ens_index: int, name_len: int = 8):
        """
        Decode the ancillary data for the Configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param ens_index: Ensemble index to store the data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.current_system[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 0, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.status_2[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.burst_index[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

    def decode_systemsetup_data(self, ens_bytes: list, ens_index: int, name_len: int = 8):
        """
        Decode the system setup data for the Configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param ens_index: Ensemble index to store the data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.bt_samples_per_second[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 0, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.bt_system_freq_hz[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.bt_cpce[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.bt_nce[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.bt_repeat_n[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.wp_samples_per_second[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        #self.wp_system_freq_hz.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.wp_cpce[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.wp_nce[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.wp_repeat_n[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.wp_lag_samples[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.bt_broadband[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.bt_lag_length[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 14, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.bt_narrowband[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 15, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.bt_beam_mux[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.wp_broadband[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 17, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.lag_cm[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 18, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 100.0
        self.wp_transmit_bandwidth[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 19, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.wp_receive_bandwidth[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 20, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.wp_beam_mux[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 22, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

        # Use the same as lag
        self.lag_near_bottom[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 18, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 100.0

        # Assume always a 20 degree beam angle for now
        beam_angle = 20

        # Get the speed of sound from this ensemble or previous
        speed_of_sound = 1500
        if not np.isnan(self.speed_of_sound[ens_index]):
            speed_of_sound = self.speed_of_sound[ens_index]
        elif ens_index-1 >= 0 and not np.isnan(self.speed_of_sound[ens_index-1]):
            speed_of_sound = self.speed_of_sound[ens_index-1]

        sample_rate = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        lag_samples = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        cpce = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        nce = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        repeats_n = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        sys_freq_hz = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        meters_per_sample = math.cos(math.pi * (beam_angle/180.0)) * speed_of_sound / 2 / sample_rate
        lag_m = lag_samples * meters_per_sample
        meters_per_cycle = math.cos(math.pi * (beam_angle/180.0)) * speed_of_sound / 2 / sys_freq_hz
        xmt_m = cpce * nce * repeats_n * meters_per_cycle
        self.xmit_pulse_cm[ens_index] = xmt_m * 100.0

    def decode_bottom_track_data(self, ens_bytes: list, ens_index: int, name_len: int = 8):
        """
        Decode the system Bottom Track data for the Configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param ens_index: Ensemble index to store the data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.bt_first_ping_time[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 0, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.bt_last_ping_time[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.bt_speed_of_sound[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.bt_status[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.bt_num_beams[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
        self.bt_actual_ping_count[ens_index] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes)


class Sensor:
    """
    System sensor data is all the data from the sensors within the ADCP.  This includes compass and
    temperature sensor.
    """

    def __init__(self, pd0_format: bool = False):
        """
        Initialize all the values

        Set the flag if using PD0 format data.  This will change the scale of the pressure sensor and orientation
        of the roll value.


        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.pd0_format = pd0_format

        self.heading = []                          # Heading in degrees.
        self.pitch = []                            # Pitch in degrees.
        self.roll = []                             # Roll in degrees.
        self.water_temp = []                       # Water Temperature in fahrenheit
        self.system_temp = []                      # System Temperature in fahrenheit

        self.pressure = []                         # Pressure from pressure sensor in Pascals
        self.transducer_depth = []                 # Transducer Depth, used by Pressure sensor in meters

        self.voltage = []                          # Voltage input to ADCP
        self.xmt_voltage = []                      # Transmit Voltage
        self.transmit_boost_neg_volt = []          # Transmitter Boost Negative Voltage

        self.raw_mag_field_strength = []           # Raw magnetic field strength (uT) (micro Tesla)
        self.raw_mag_field_strength2 = []          # Raw magnetic field strength (uT) (micro Tesla)
        self.raw_mag_field_strength3 = []          # Raw magnetic field strength (uT) (micro Tesla)
        self.pitch_gravity_vec = []                # Pitch Gravity Vector
        self.roll_gravity_vec = []                 # Roll Gravity Vector
        self.vertical_gravity_vec = []             # Vertical Gravity Vector

        self.bt_heading = []
        self.bt_pitch = []
        self.bt_roll = []
        self.bt_water_temp = []
        self.bt_system_temp = []
        self.bt_salinity = []
        self.bt_pressure = []
        self.bt_transducer_depth = []

        # ADCP 3 Values
        self.hs1_temp = []
        self.hs2_temp = []
        self.rcv1_temp = []
        self.rcv2_temp = []
        self.vinf = []
        self.vg = []
        self.vt = []
        self.vtl = []
        self.d3v3 = []
        self.bt_hs1_temp = []
        self.bt_hs2_temp = []
        self.bt_rcv1_temp = []
        self.bt_rcv2_temp = []
        self.bt_vinf = []
        self.bt_vg = []
        self.bt_vt = []
        self.bt_vtl = []
        self.bt_d3v3 = []
        self.bt_sounder_range = []
        self.bt_sounder_snr = []
        self.bt_sounder_amp = []

        self.echo_sounder_depth = []

    def decode_systemsetup_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the system setup data for the Sensor data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.voltage.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.xmt_voltage.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.transmit_boost_neg_volt.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 21, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

    def decode_ancillary_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ancillary data for the Sensor data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.heading.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.pitch.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        self.water_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.system_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        self.raw_mag_field_strength.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.raw_mag_field_strength2.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 14, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.raw_mag_field_strength3.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 15, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.pitch_gravity_vec.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.roll_gravity_vec.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 17, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.vertical_gravity_vec.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 18, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        # Convert values to PD0 format if selected
        if self.pd0_format:
            roll = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            if roll > 90.0:
                self.roll.append(-1 * (180.0 - roll))
            elif roll < -90.0:
                self.roll.append(180.0 + roll)

            pressure = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            transducer_depth = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            self.pressure.append(round(pressure * 0.0001))
            self.transducer_depth.append(round(transducer_depth * 10.0))
        else:
            self.roll.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            self.pressure.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            self.transducer_depth.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

    def decode_ancillary_adcp3_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ancillary ADCP3 data for the Sensor data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.hs1_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.hs2_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 14, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.rcv1_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 15, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.rcv2_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.vinf.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 17, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.vg.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 18, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.vt.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.vtl.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 17, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.d3v3.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 18, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

    def empty_ancillary_adcp3_init(self):
        """
        Initialize the array with NaN if no value is given.
        """
        self.hs1_temp.append(np.NaN)
        self.hs2_temp.append(np.NaN)
        self.rcv1_temp.append(np.NaN)
        self.rcv2_temp.append(np.NaN)
        self.vinf.append(np.NaN)
        self.vg.append(np.NaN)
        self.vt.append(np.NaN)
        self.vtl.append(np.NaN)
        self.d3v3.append(np.NaN)

    def decode_bottom_track_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the bottom track data for the Sensor data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.bt_heading.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_pitch.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_water_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_system_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_salinity.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        # Convert values to PD0 format if selected
        if self.pd0_format:
            bt_roll = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            if bt_roll > 90.0:
                self.bt_roll.append(-1 * (180.0 - bt_roll))
            elif bt_roll < -90.0:
                self.bt_roll.append(180.0 + bt_roll)

            bt_pressure = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            bt_transducer_depth = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            self.bt_pressure = round(bt_pressure * 0.0001)
            self.bt_transducer_depth = round(bt_transducer_depth * 10.0)
        else:
            self.bt_roll.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            self.bt_pressure.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            self.bt_transducer_depth.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

    def decode_bottom_track_adcp3_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the bottom track ADCP3 data for the Sensor data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Get the number of beams
        num_beams = int(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        # 14 raw values plus 15 values for each beam
        data_index = 14 + (15 * num_beams)

        self.bt_hs1_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 1), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_hs2_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 2), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_rcv1_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 3), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_rcv2_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 4), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_vinf.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 5), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_vg.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 6), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_vt.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 7), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_vtl.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 8), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_d3v3.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 9), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_sounder_range.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 11), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_sounder_snr.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 12), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_sounder_amp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 13), RtbRowe.BYTES_IN_FLOAT, ens_bytes))

    def empty_bt_init(self, num_beams: int):
        """
        Set the list with NAN for all missing Bottom Track data.
        :param num_beams Number of ensembles.
        """
        self.bt_heading.append(np.NaN)
        self.bt_pitch.append(np.NaN)
        self.bt_roll.append(np.NaN)
        self.bt_water_temp.append(np.NaN)
        self.bt_system_temp.append(np.NaN)
        self.bt_salinity.append(np.NaN)
        self.bt_pressure.append(np.NaN)
        self.bt_transducer_depth.append(np.NaN)

    def empty_bt_adcp3_init(self, num_beams: int):
        """
        If now Bottom Track ADCP3 data is given,
        fill in the arrays with NaN values.
        :param num_beams Number of beams.
        """
        self.bt_hs1_temp.append(np.NaN)
        self.bt_hs2_temp.append(np.NaN)
        self.bt_rcv1_temp.append(np.NaN)
        self.bt_rcv2_temp.append(np.NaN)
        self.bt_vinf.append(np.NaN)
        self.bt_vg.append(np.NaN)
        self.bt_vt.append(np.NaN)
        self.bt_vtl.append(np.NaN)
        self.bt_d3v3.append(np.NaN)
        self.bt_sounder_range.append(np.NaN)
        self.bt_sounder_snr.append(np.NaN)
        self.bt_sounder_amp.append(np.NaN)


class BT:
    """
    Bottom Tracking used to measure the depth and vessel speed (Speed over Ground).
    """
    def __init__(self, num_ens: int, num_beams: int, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the scale will change from percentage to counts.
        The value has to be converted from
        :param num_ens: Number of ensembles.
        :param num_beams: Number of velocity beams.
        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.num_beams = 0

        self.corr = RtbRowe.nans([num_beams, num_ens])
        self.depth_m = RtbRowe.nans([num_beams, num_ens])
        self.eval_amp = RtbRowe.nans([num_beams, num_ens])
        self.ext_depth_cm = RtbRowe.nans(num_ens)
        self.pergd = RtbRowe.nans([num_beams, num_ens])
        self.rssi = RtbRowe.nans([num_beams, num_ens])
        self.snr = RtbRowe.nans([num_beams, num_ens])
        self.vel_mps = RtbRowe.nans([num_beams, num_ens])
        self.instr_vel = RtbRowe.nans([num_beams, num_ens])
        self.instr_good = RtbRowe.nans([num_beams, num_ens])
        self.earth_vel = RtbRowe.nans([num_beams, num_ens])
        self.earth_good = RtbRowe.nans([num_beams, num_ens])
        self.pulse_coh_snr = RtbRowe.nans([num_beams, num_ens])
        self.pulse_coh_amp = RtbRowe.nans([num_beams, num_ens])
        self.pulse_coh_vel = RtbRowe.nans([num_beams, num_ens])
        self.pulse_coh_noise = RtbRowe.nans([num_beams, num_ens])
        self.pulse_coh_corr = RtbRowe.nans([num_beams, num_ens])

        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, ens_index: int, name_len: int = 8):
        """
        Decode the ensemble data for the Bottom Traack data.

        Initialize the list of Bottom Track data.  [beam]

        :param ens_bytes: Byte array containing the Bottom Track data.
        :param ens_index: Ensemble index to store the data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Get the number of beams
        self.num_beams = int(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        # Get the ping count
        # Value stored in Cfg but needed for conversion to PD0
        bt_actual_ping_count = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

        # Initialize the array
        snr = np.empty(shape=[self.num_beams], dtype=np.float)
        depth = np.empty(shape=[self.num_beams], dtype=np.float)
        amp = np.empty(shape=[self.num_beams], dtype=np.float)
        corr = np.empty(shape=[self.num_beams], dtype=np.float)
        beam_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        beam_good = np.empty(shape=[self.num_beams], dtype=np.int)
        instr_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        instr_good = np.empty(shape=[self.num_beams], dtype=np.int)
        earth_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        earth_good = np.empty(shape=[self.num_beams], dtype=np.int)
        pulse_coh_snr = np.empty(shape=[self.num_beams], dtype=np.float)
        pulse_coh_amp = np.empty(shape=[self.num_beams], dtype=np.float)
        pulse_coh_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        pulse_coh_noise = np.empty(shape=[self.num_beams], dtype=np.float)
        pulse_coh_corr = np.empty(shape=[self.num_beams], dtype=np.float)

        # Index to start at for the following data
        index = 14

        # Range Values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                depth[beam] = value
            else:
                # PD0 data
                # Check for bad velocity and convert
                if RtbRowe.is_bad_velocity(value):
                    value = RtbRowe.PD0_BAD_VEL
                else:
                    # Convert from m to cm
                    value = round(value * 100.0)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:
                    depth[0] = value
                if beam == 0:
                    depth[3] = value
                elif beam == 1:
                    depth[2] = value
                elif beam == 2:
                    depth[0] = value
                elif beam == 3:
                    depth[1] = value

            # Increment for the next beam
            index += 1

        # Add the data the numpy array [:num_beams, ens_index]
        self.depth_m[:self.num_beams, ens_index] = depth.T

        # SNR values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                snr[beam] = value
            else:
                # PD0 data
                # Convert from db to counts (0.5 counts per dB)
                value = round(value * 2.0)

                # Check for bad value
                if value > RtbRowe.PD0_BAD_AMP:
                    value = RtbRowe.PD0_BAD_AMP

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:
                    snr[0] = value
                elif beam == 0:
                    snr[3] = value
                elif beam == 1:
                    snr[2] = value
                elif beam == 2:
                    snr[0] = value
                elif beam == 3:
                    snr[1] = value

            # Increment for the next beam
            index += 1

        # Add the data the numpy array [:num_beams, ens_index]
        self.snr[:self.num_beams, ens_index] = snr.T

        # Amplitude values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                amp[beam] = value
            else:
                # PD0 data
                # Convert from db to counts (0.5 counts per dB)
                value = round(value * 2.0)

                # Check for bad value
                if value > RtbRowe.PD0_BAD_AMP:
                    value = RtbRowe.PD0_BAD_AMP

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:
                    amp[0] = value
                elif beam == 0:
                    amp[3] = value
                elif beam == 1:
                    amp[2] = value
                elif beam == 2:
                    amp[0] = value
                elif beam == 3:
                    amp[1] = value

            # Increment for the next beam
            index += 1

        # Add the data the numpy array [:num_beams, ens_index]
        self.rssi[:self.num_beams, ens_index] = amp.T

        # Correlation values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                corr[beam] = value
            else:
                # PD0 data
                # Convert from percentage to 0-255 counts
                value = round(value * 255.0)

                # Check for bad value
                if value > RtbRowe.PD0_BAD_AMP:
                    value = RtbRowe.PD0_BAD_AMP

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:             # Vertical beam
                    corr[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 3
                    corr[3] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 2
                    corr[2] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam 0
                    corr[0] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 1
                    corr[1] = value

            # Increment for the next beam
            index += 1

        # Add the data the numpy array [:num_beams, ens_index]
        self.corr[:self.num_beams, ens_index] = corr.T

        # Beam Velocity values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            # Check for bad velocity and convert
            if RtbRowe.is_bad_velocity(value):
                value = np.nan

            if not self.pd0_format:
                # Store RTB data
                beam_vel[beam] = value
            else:
                # PD0 data
                # Check for bad velocity and convert
                if not np.isnan(value):
                    # Convert from m/s to mm/s
                    # Also invert the direction
                    value = round(value * 1000.0 * -1)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:             # Vertical beam
                    beam_vel[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 3
                    beam_vel[3] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 2
                    beam_vel[2] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam 0
                    beam_vel[0] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 1
                    beam_vel[1] = value

            # Increment for the next beam
            index += 1

        # Add the data the numpy array [:num_beams, ens_index]
        self.vel_mps[:self.num_beams, ens_index] = beam_vel.T

        # Beam Good Pings values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                beam_good[beam] = int(value)
            else:
                # PD0 data
                # Check for bad velocity and convert
                if RtbRowe.is_bad_velocity(value):
                    value = RtbRowe.PD0_BAD_VEL
                else:
                    # Convert from number of good pings to a percentage of good pings
                    value = round((value * 100.0) / bt_actual_ping_count)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:             # Vertical beam
                    beam_good[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 3
                    beam_good[3] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 2
                    beam_good[2] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam 0
                    beam_good[0] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 1
                    beam_good[1] = value

            # Increment for the next beam
            index += 1

        # Add the data the numpy array [:num_beams, ens_index]
        self.pergd[:self.num_beams, ens_index] = beam_good.T

        # Instrument Velocity values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            # Check for bad velocity and convert
            if RtbRowe.is_bad_velocity(value):
                value = np.nan

            if not self.pd0_format:
                # Store RTB data
                instr_vel[beam] = value
            else:
                # PD0 data
                # Check for bad velocity and convert
                if not np.isnan(value):
                    # Convert from m/s to mm/s
                    # Also invert the direction
                    value = round(value * 1000.0 * -1)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 XYZ order 1,0,-2,3
                if self.num_beams == 1:             # Vertical beam
                    instr_vel[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 1
                    instr_vel[1] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 0
                    instr_vel[0] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam -2
                    instr_vel[2] = value * -1.0
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 3
                    instr_vel[3] = value

            # Increment for the next beam
            index += 1

        # Add the data the numpy array [:num_beams, ens_index]
        self.instr_vel[:self.num_beams, ens_index] = instr_vel.T

        # Instrument Good Pings values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                instr_good[beam] = int(value)
            else:
                # PD0 data
                # Check for bad velocity and convert
                if RtbRowe.is_bad_velocity(value):
                    value = RtbRowe.PD0_BAD_VEL
                else:
                    # Convert from number of good pings to a percentage of good pings
                    value = round((value * 100.0) / bt_actual_ping_count)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 XYZ order 1,0,-2,3
                if self.num_beams == 1:             # Vertical beam
                    instr_good[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 1
                    instr_good[1] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 0
                    instr_good[0] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam -2
                    instr_good[2] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 3
                    instr_good[3] = value

            # Increment for the next beam
            index += 1

        # Add the data the numpy array [:num_beams, ens_index]
        self.instr_good[:self.num_beams, ens_index] = instr_good.T

        # Earth Velocity values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            # Check for bad velocity and convert
            if RtbRowe.is_bad_velocity(value):
                value = np.nan

            if not self.pd0_format:
                # Store RTB data
                earth_vel[beam] = value
            else:
                # PD0 data
                # Check for bad velocity and convert
                if not np.isnan(value):
                    # Convert from m/s to mm/s
                    # Also invert the direction
                    value = round(value * 1000.0 * -1)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:             # Vertical beam
                    earth_vel[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 0
                    earth_vel[0] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 1
                    earth_vel[1] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam 2
                    earth_vel[2] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 3
                    earth_vel[3] = value

            # Increment for the next beam
            index += 1

        # Add the data the numpy array [:num_beams, ens_index]
        self.earth_vel[:self.num_beams, ens_index] = earth_vel.T

        # Earth Good Pings values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                earth_good[beam] = int(value)
            else:
                # PD0 data
                # Check for bad velocity and convert
                if RtbRowe.is_bad_velocity(value):
                    value = RtbRowe.PD0_BAD_VEL
                else:
                    # Convert from number of good pings to a percentage of good pings
                    value = round((value * 100.0) / bt_actual_ping_count)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 XYZ order 0,1,2,3
                if self.num_beams == 1:             # Vertical beam
                    earth_good[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 0
                    earth_good[0] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 1
                    earth_good[1] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam 2
                    earth_good[2] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 3
                    earth_good[3] = value

            # Increment for the next beam
            index += 1

        # Add the data the numpy array [:num_beams, ens_index]
        self.earth_good[:self.num_beams, ens_index] = earth_good.T

        # Pulse Coherent SNR values
        for beam in range(self.num_beams):
            pulse_coh_snr[beam] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            index += 1

        # Add the data the numpy array [:num_beams, ens_index]
        self.pulse_coh_snr[:self.num_beams, ens_index] = pulse_coh_snr.T

        # Pulse Coherent Amplitude values
        for beam in range(self.num_beams):
            pulse_coh_amp[beam] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            index += 1

        # Add the data the numpy array [:num_beams, ens_index]
        self.pulse_coh_amp[:self.num_beams, ens_index] = pulse_coh_amp.T

        # Pulse Coherent Velocity values
        for beam in range(self.num_beams):
            pulse_coh_vel[beam] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            index += 1

        # Add the data the numpy array [:num_beams, ens_index]
        self.pulse_coh_vel[:self.num_beams, ens_index] = pulse_coh_vel.T

        # Pulse Coherent Noise values
        for beam in range(self.num_beams):
            pulse_coh_noise[beam] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            index += 1

        # Add the data the numpy array [:num_beams, ens_index]
        self.pulse_coh_noise[:self.num_beams, ens_index] = pulse_coh_noise.T

        # Pulse Coherent Correlation values
        for beam in range(self.num_beams):
            pulse_coh_corr[beam] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            index += 1

        # Add the data the numpy array [:num_beams, ens_index]
        self.pulse_coh_corr[:self.num_beams, ens_index] = pulse_coh_corr.T


class RT:
    """
    Range Tracking values to measure the surface when upward looking.
    When downward looking, values are used as an echo sounder using
    the profile ping.
    """
    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the scale will change from percentage to counts.
        The value has to be converted from
        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.num_beams = 0
        self.snr = []
        self.depth = []
        self.pings = []
        self.amp = []
        self.corr = []
        self.beam_vel = []
        self.instr_vel = []
        self.earth_vel = []

        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ensemble data for the Range Tracking data.

        Initialize the list of Range Tracking data.  [beam]

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Get the number of beams
        self.num_beams = int(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 0, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        # Initialize the array
        snr = np.empty(shape=[self.num_beams], dtype=np.float)
        depth = np.empty(shape=[self.num_beams], dtype=np.float)
        pings = np.empty(shape=[self.num_beams], dtype=np.float)
        amp = np.empty(shape=[self.num_beams], dtype=np.float)
        corr = np.empty(shape=[self.num_beams], dtype=np.float)
        beam_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        instr_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        earth_vel = np.empty(shape=[self.num_beams], dtype=np.float)

        if self.num_beams == 4:
            snr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            snr[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            snr[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            snr[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            depth[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            depth[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            depth[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            depth[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            pings[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            pings[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            pings[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            pings[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            amp[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            amp[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 14, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            amp[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 15, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            amp[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            corr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 17, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            corr[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 18, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            corr[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 19, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            corr[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 20, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            beam_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 21, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            beam_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 22, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            beam_vel[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 23, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            beam_vel[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 24, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            instr_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 25, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            instr_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 26, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            instr_vel[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 27, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            instr_vel[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 28, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            earth_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 29, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            earth_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 30, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            earth_vel[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 31, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            earth_vel[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 32, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        elif self.num_beams == 3:
            snr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            snr[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            snr[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            depth[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            depth[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            depth[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            pings[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            pings[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            pings[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            amp[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            amp[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            amp[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            corr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            corr[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 14, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            corr[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 15, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            beam_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            beam_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 17, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            beam_vel[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 18, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            instr_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 19, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            instr_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 20, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            instr_vel[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 21, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            earth_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 22, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            earth_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 23, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            earth_vel[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 24, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        elif self.num_beams == 2:
            snr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            snr[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            depth[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            depth[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            pings[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            pings[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            amp[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            amp[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            corr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            corr[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            beam_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            beam_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            instr_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            instr_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 14, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            earth_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 15, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            earth_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        elif self.num_beams == 1:
            snr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            depth[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            pings[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            amp[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            corr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            beam_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            instr_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            earth_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        # Add the data to the lis
        self.snr.append(snr)
        self.depth.append(depth)
        self.pings.append(pings)
        self.amp.append(amp)
        self.corr.append(corr)
        self.beam_vel.append(beam_vel)
        self.instr_vel.append(instr_vel)
        self.earth_vel.append(earth_vel)


class Nmea:
    """
    NMEA data from the ensemble dataset.
    """
    def __init__(self, pd0_format: bool = False):
        """
        Initialize all the values.

        Initializing the lists as list and converting
        to numpy array after data is decoded.
        """
        self.pd0_format = pd0_format

        self.gga = []
        self.gsa = []
        self.vtg = []
        self.dbt = []
        self.hdt = []

        # GGA
        self.gga_delta_time = []            # float
        self.gga_header = []                # str
        self.utc = []                       # float
        self.lat_deg = []                   # float
        self.lat_ref = []                   # str
        self.lon_deg = []                   # float
        self.lon_ref = []                   # str
        self.corr_qual = []                 # float
        self.num_sats = []                  # int
        self.hdop = []                      # float
        self.alt = []                       # float
        self.alt_unit = []                  # str
        self.geoid = []                     # str
        self.geoid_unit = []                # str
        self.d_gps_age = []                 # float
        self.ref_stat_id = []               # float

        # VTG
        self.vtg_delta_time = []            # float
        self.vtg_header = []                # str
        self.course_true = []               # float
        self.true_indicator = []            # str
        self.course_mag = []                # float
        self.mag_indicator = []             # str
        self.speed_knots = []               # float
        self.knots_indicator = []           # str
        self.speed_kph = []                 # float
        self.kph_indicator = []             # str
        self.mode_indicator = []            # str

        # HDT
        self.hdt_header = []
        self.heading = []
        self.rel_true_north = []

        # Temp variables to accumulate with each new ensemble
        self.temp_gga = []
        self.temp_gsa = []
        self.temp_vtg = []
        self.temp_dbt = []
        self.temp_hdt = []

    def decode(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the NMEA dataset.  This will be the raw NMEA messages
        from the ADCP containing GPS data.
        :param ens_bytes Bytes for dataset.
        :param name_len: Name length to get the start location.
        """
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Convert all the messages to a string
        nmea_str = str(ens_bytes[packet_pointer:], "UTF-8")

        # Clear the lists
        self.temp_gga.clear()
        self.temp_gsa.clear()
        self.temp_vtg.clear()
        self.temp_dbt.clear()
        self.temp_hdt.clear()

        # Decode each NMEA message
        for msg in nmea_str.split():
            self.decode_nmea(msg)

        # Convert all the list to numpy array for better storage
        # Add the data to the list
        self.gga.append(np.array(self.temp_gga))
        self.gsa.append(np.array(self.temp_gsa))
        self.vtg.append(np.array(self.temp_vtg))
        self.dbt.append(np.array(self.temp_dbt))
        self.hdt.append(np.array(self.temp_hdt))

        # Decode the last messages
        if len(self.temp_gga) > 0:
            self.decode_gga(self.temp_gga[-1])
        else:
            self.decode_gga(None)

        if len(self.temp_vtg) > 0:
            self.decode_vtg(self.temp_vtg[-1])
        else:
            self.decode_vtg(None)

        if len(self.temp_hdt) > 0:
            self.decode_hdt(self.temp_hdt[-1])
        else:
            self.decode_hdt(None)

    def decode_nmea(self, nmea_str: str):
        """
        Verify the NMEA message is by checking the checksum.
        Then add the message to the list and decode each message.
        :param nmea_str NMEA string to decode.
        """

        # Verify the NMEA string is good
        if Nmea.check_nmea_checksum(nmea_str):
            # Add each message to the list
            # Decode the data
            if 'gga' in  nmea_str or 'GGA' in nmea_str:
                self.temp_gga.append(nmea_str)
            if 'gsa' in nmea_str or 'GSA' in nmea_str:
                self.temp_gsa.append(nmea_str)
            if 'vtg' in nmea_str or 'VTG' in nmea_str:
                self.temp_vtg.append(nmea_str)
            if 'dbt' in nmea_str or 'DBT' in nmea_str:
                self.temp_dbt.append(nmea_str)
            if 'hdt' in nmea_str or 'HDT' in nmea_str:
                self.temp_hdt.append(nmea_str)

    def decode_gga(self, nmea_str: str):
        """
        Decode GGA message.  Update the variables.

        :param nmea_str NMEA string.
        """
        try:
            if nmea_str:
                temp_array = np.array(nmea_str.split(','))
                temp_array[temp_array == '999.9'] = ''

                #self.gga_delta_time = delta_time
                self.gga_header.append(temp_array[0])
                self.utc.append(float(temp_array[1]))
                lat_str = temp_array[2]
                lat_deg = float(lat_str[0:2])
                lat_deg = lat_deg + float(lat_str[2:]) / 60
                self.lat_deg.append(lat_deg)
                self.lat_ref.append(temp_array[3])
                lon_str = temp_array[4]
                lon_num = float(lon_str)
                lon_deg = np.floor(lon_num / 100)
                lon_deg = lon_deg + (((lon_num / 100.) - lon_deg) * 100.) / 60.
                self.lon_deg.append(lon_deg)
                self.lon_ref.append(temp_array[5])
                self.corr_qual.append(float(temp_array[6]))
                self.num_sats.append(float(temp_array[7]))
                self.hdop.append(float(temp_array[8]))
                self.alt.append(float(temp_array[9]))
                self.alt_unit.append(temp_array[10])
                self.geoid.append(temp_array[11])
                self.geoid_unit.append(temp_array[12])
                self.d_gps_age.append(float(temp_array[13]))
                idx_star = temp_array[14].find('*')
                self.ref_stat_id.append(float(temp_array[15][:idx_star]))
            else:
                self.gga_header.append(np.NaN)
                self.utc.append(np.NaN)
                self.lat_deg.append(np.NaN)
                self.lat_ref.append(np.NaN)
                self.lon_deg.append(np.NaN)
                self.lon_ref.append(np.NaN)
                self.corr_qual.append(np.NaN)
                self.num_sats.append(np.NaN)
                self.hdop.append(np.NaN)
                self.alt.append(np.NaN)
                self.alt_unit.append(np.NaN)
                self.geoid.append(np.NaN)
                self.geoid_unit.append(np.NaN)
                self.d_gps_age.append(np.NaN)
                self.ref_stat_id.append(np.NaN)

        except (ValueError, EOFError, IndexError):
            pass

    def decode_vtg(self, nmea_str: str):
        """
        Decode the VTG message and set all the variables.

        :param nmea_str: NMEA string.
        """
        try:
            if nmea_str:
                temp_array = np.array(nmea_str.split(','))
                temp_array[temp_array == '999.9'] = ''

                #self.vtg_delta_time = delta_time
                self.vtg_header.append(temp_array[0])
                self.course_true.append(Nmea.valid_number(temp_array[1]))
                self.true_indicator.append(temp_array[2])
                self.course_mag.append(Nmea.valid_number(temp_array[3]))
                self.mag_indicator.append(temp_array[4])
                self.speed_knots.append(Nmea.valid_number(temp_array[5]))
                self.knots_indicator.append(temp_array[6])
                self.speed_kph.append(Nmea.valid_number(temp_array[7]))
                self.kph_indicator.append(temp_array[8])
                idx_star = temp_array[9].find('*')
                self.mode_indicator.append(temp_array[9][:idx_star])
            else:
                self.vtg_header.append(np.NaN)
                self.course_true.append(np.NaN)
                self.true_indicator.append(np.NaN)
                self.course_mag.append(np.NaN)
                self.mag_indicator.append(np.NaN)
                self.speed_knots.append(np.NaN)
                self.knots_indicator.append(np.NaN)
                self.speed_kph.append(np.NaN)
                self.kph_indicator.append(np.NaN)
                self.mode_indicator.append(np.NaN)

        except (ValueError, EOFError, IndexError):
            pass

    def decode_hdt(self, nmea_str: str):
        """
        Decode the HDT message and set all the variables.

        :param nmea_str: NMEA string.
        """
        try:
            if nmea_str:
                temp_array = np.array(nmea_str.split(','))
                temp_array[temp_array == '999.9'] = ''

                # self.vtg_delta_time = delta_time
                self.hdt_header.append(temp_array[0])
                self.heading.append(Nmea.valid_number(temp_array[1]))
                idx_star = temp_array[2].find('*')
                self.rel_true_north.append(temp_array[2][:idx_star])
            else:
                self.hdt_header.append(np.NaN)
                self.heading.append(np.NaN)
                self.rel_true_north.append(np.NaN)

        except (ValueError, EOFError, IndexError):
            pass

    @staticmethod
    def valid_number(data_in):
        """
        Check to see if data_in can be converted to float.

        :param data_in: str String to be converted to float
        :return Returns a float of data_in or nan if conversion is not possible
        """

        try:
            data_out = float(data_in)
        except ValueError:
            data_out = np.nan
        return data_out

    @staticmethod
    def check_nmea_checksum(nmea_str: str):
        """
        Calculate the NMEA checksum.  Verify the
        checksum value matches the given value.
        :param nmea_str NMEA string.
        :return TRUE = Good checksum
        """
        try:
            # Remove newline and spaces at the end
            nmea_str = nmea_str.rstrip('\n')
            # Get the checksum value
            checksum = nmea_str[len(nmea_str) - 2:]
            checksum = int(checksum, 16)

            # Get the data from the string
            nmea_data = re.sub("(\n|\r\n)", "", nmea_str[nmea_str.find("$") + 1:nmea_str.find("*")])

            # Calculate the checksum
            calc_checksum = 0
            for c in nmea_data:
                calc_checksum ^= ord(c)
            calc_checksum = calc_checksum & 0xFF

            # Verify the checksum matches
            if calc_checksum == checksum:
                return True

            return False
        except Exception as ex:
            logging.error(ex)
            return False


class Gage:
    """
    Gage Height data from the ensemble dataset.
    """
    def __init__(self, pd0_format: bool = False):
        """
        Initialize all the values.

        Initializing the lists as list and converting
        to numpy array after data is decoded.
        """
        self.pd0_format = pd0_format

        self.status = []
        self.avg_range = []
        self.sd = []
        self.avg_sn = []
        self.n = []
        self.salinity = []
        self.pressure = []
        self.depth = []
        self.water_temp = []
        self.backplane_temp = []
        self.speed_of_sound = []
        self.heading = []
        self.pitch = []
        self.roll = []
        self.avg_s = []
        self.avg_n1 = []
        self.avg_n2 = []
        self.gain_frac = []

        self.pings = []
        self.snr_thresh = []
        self.gain_thresh = []
        self.stat_thresh = []
        self.xmt_cycles = []
        self.depth_offset = []

    def decode_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ancillary data for the Configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.status.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 0, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.avg_range.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.sd.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.avg_sn.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.n.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.salinity.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.pressure.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.depth.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.water_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.backplane_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.speed_of_sound.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.heading.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.pitch.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.roll.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.avg_s.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 14, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.avg_n1.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 15, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.avg_n2.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.gain_frac.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 17, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.pings.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 18, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.snr_thresh.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 19, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.gain_thresh.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 20, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.stat_thresh.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 21, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.xmt_cycles.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 22, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.depth_offset.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 23, RtbRowe.BYTES_IN_FLOAT, ens_bytes))


class RiverBT:
    """
    River Bottom Track data from the ensemble dataset.
    """
    def __init__(self, pd0_format: bool = False):
        """
        Initialize all the values.

        Initializing the lists as list and converting
        to numpy array after data is decoded.
        """
        self.pd0_format = pd0_format

        self.num_subsystems = []                # Number of subsystems to decode
        self.ping_count = []                    # Pings averaged
        self.status = []                        # Data status
        self.beams = []                         # Number of beams
        self.nce = []                           # Number of code elements
        self.repeats_n = []                     # Number of code repeats
        self.cpce = []                          # Codes per code elements
        self.bb = []                            # Broadband
        self.ll = []
        self.beam_mux = []                      # Beam Mux setup
        self.nb = []                            # Narrowband
        self.ping_sec = []                      # Ping time in seconds
        self.heading = []                       # Heading 0 to 360
        self.pitch = []                         # Pitch -90 to 90
        self.roll = []                          # Roll -180 to 180
        self.water_temp = []                    # Water Temperature in C
        self.backplane_temp = []                # Internal System temperature in C
        self.salinity = []                      # Salinity in PPT
        self.pressure = []                      # Pressure in Pascal
        self.depth = []                         # Pressure converted to m
        self.speed_of_sound = []                # Speed of Sound in m/s
        self.mx = []
        self.my = []
        self.mz = []
        self.gp = []
        self.gr = []
        self.gz = []
        self.samples_per_sec = []               # Samples per second
        self.system_freq_hz = []                # System frequency in Hz
        self.bt_range = []                      # Bottom Track Range in m
        self.bt_snr = []                        # Bottom Track SNR in dB
        self.bt_amp = []                        # Bottom Track Amplitude in dB
        self.bt_noise_amp_bp = []               # Noise in Amplitude Back Porch
        self.bt_noise_amp_fp = []               # Noise in Amplitude Front Porch
        self.bt_corr = []                       # Bottom Track Correlation in percent
        self.vel = []                           # Bottom Track Beam Velocity in m/s
        self.beam_n = []

    def decode_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the River Bottom data data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """

        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        num_subsystems = int(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 0, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.num_subsystems.append(num_subsystems)

        # Start of the data
        index = 1

        # Create a temp list to hold all the values for each subsystem
        # Accumulate the list then add it to the data type
        # Index will keep track of where we are located in the data
        pint_count = []
        for sb in range(num_subsystems):
            pint_count.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.ping_count.append(pint_count)

        status = []
        for sb in range(num_subsystems):
            status.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.status.append(status)

        beams = []
        for sb in range(num_subsystems):
            beams.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.beams.append(beams)

        nce = []
        for sb in range(num_subsystems):
            nce.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.nce.append(nce)

        repeats_n = []
        for sb in range(num_subsystems):
            repeats_n.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.repeats_n.append(repeats_n)

        cpce = []
        for sb in range(num_subsystems):
            cpce.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.cpce.append(cpce)

        bb = []
        for sb in range(num_subsystems):
            bb.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.bb.append(bb)

        ll = []
        for sb in range(num_subsystems):
            ll.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.ll.append(ll)

        beam_mux = []
        for sb in range(num_subsystems):
            beam_mux.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.beam_mux.append(beam_mux)

        nb = []
        for sb in range(num_subsystems):
            nb.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.nb.append(nb)

        ps = []
        for sb in range(num_subsystems):
            ps.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.ping_sec.append(ps)

        hdg = []
        for sb in range(num_subsystems):
            hdg.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.heading.append(hdg)

        ptch = []
        for sb in range(num_subsystems):
            ptch.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.pitch.append(ptch)

        roll = []
        for sb in range(num_subsystems):
            roll.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.roll.append(roll)

        wt = []
        for sb in range(num_subsystems):
            wt.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.water_temp.append(wt)

        sys_temp = []
        for sb in range(num_subsystems):
            sys_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.backplane_temp.append(sys_temp)

        sal = []
        for sb in range(num_subsystems):
            sal.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.salinity.append(sal)

        pres = []
        for sb in range(num_subsystems):
            pres.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.pressure.append(pres)

        depth = []
        for sb in range(num_subsystems):
            depth.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.depth.append(depth)

        sos = []
        for sb in range(num_subsystems):
            sos.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.speed_of_sound.append(sos)

        mx = []
        for sb in range(num_subsystems):
            mx.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.mx.append(mx)

        my = []
        for sb in range(num_subsystems):
            my.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.my.append(my)

        mz = []
        for sb in range(num_subsystems):
            mz.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.mz.append(mz)

        gp = []
        for sb in range(num_subsystems):
            gp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.gp.append(gp)

        gr = []
        for sb in range(num_subsystems):
            gr.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.gr.append(gr)

        gz = []
        for sb in range(num_subsystems):
            gz.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.gz.append(gz)

        sps = []
        for sb in range(num_subsystems):
            sps.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.samples_per_sec.append(sps)

        freq = []
        for sb in range(num_subsystems):
            freq.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.system_freq_hz.append(freq)

        bt_range = []
        for sb in range(num_subsystems):
            bt_range.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.bt_range.append(bt_range)

        snr = []
        for sb in range(num_subsystems):
            snr.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.bt_snr.append(snr)

        amp = []
        for sb in range(num_subsystems):
            amp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.bt_amp.append(amp)

        noise_bp = []
        for sb in range(num_subsystems):
            noise_bp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.bt_noise_amp_bp.append(noise_bp)

        noise_fp = []
        for sb in range(num_subsystems):
            noise_fp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.bt_noise_amp_fp.append(noise_fp)

        corr = []
        for sb in range(num_subsystems):
            corr.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.bt_corr.append(corr)

        vel = []
        for sb in range(num_subsystems):
            vel.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.vel.append(vel)

        beam_n = []
        for sb in range(num_subsystems):
            beam_n.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.beam_n.append(beam_n)


class Surface:
    """
    Surf data are to accommodate RiverRay and RiverPro.  pd0_read sets these
    values to nan when reading Rio Grande or StreamPro data
    """

    def __init__(self, num_ens: int, num_beams: int, max_surface_bins: int):
        """
        Initialize all the values.

        :param num_ens: Number of ensembles in the file.
        :param num_beams: Number of beams on the system.
        :param max_surface_bins: Number of surface bins.
        """
        self.no_cells = RtbRowe.nans(num_ens)                                       # Number of surface cells in the ensemble
        self.cell_size_cm = RtbRowe.nans(num_ens)                                   # Cell size in cm
        self.dist_bin1_cm = RtbRowe.nans(num_ens)                                   # Distance to center of cell 1 in cm
        self.vel_mps = np.tile([np.nan], [num_beams, max_surface_bins, num_ens])    # 3D array of velocity data in each cell and ensemble
        self.corr = RtbRowe.nans([num_beams, max_surface_bins, num_ens])            # 3D array of correlation data for each beam, cell, and ensemble
        self.pergd = RtbRowe.nans([num_beams, max_surface_bins, num_ens])           # 3D array of percent good data for each beam, cell, and ensemble
        self.rssi = RtbRowe.nans([num_beams, max_surface_bins, num_ens])            # 3D array of signal strength data for each beam, cell, and ensemble





