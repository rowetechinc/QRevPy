import numpy as np
from Classes.SelectFit import SelectFit
from Classes.ExtrapQSensitivity import ExtrapQSensitivity
from Classes.NormData import NormData


class ComputeExtrap(object):
    """Class to compute the optimized or manually specified extrapolation methods

    Attributes
    ----------
    threshold: float
        Threshold as a percent for determining if a median is valid
    subsection: list
        Percent of discharge, does not account for transect direction
    fit_method: str
        Method used to determine fit.  Automatic or manual
    norm_data: NormData
        Object of class NormData
    sel_fit: SelectFit
        Object of class SelectFit
    q_sensitivity: ExtrapQSensitivity
        Object of class ExtrapQSensitivity
    messages: str
        Variable for messages to UserWarning

    """
    
    def __init__(self):
        """Initialize instance variables."""

        self.threshold = None  # Threshold as a percent for determining if a median is valid
        self.subsection = None  # Percent of discharge, does not account for transect direction
        self.fit_method = None  # Method used to determine fit.  Automatic or manual
        self.norm_data = []  # Object of class norm data
        self.sel_fit = []  # Object of class SelectFit
        self.q_sensitivity = None  # Object of class ExtrapQSensitivity
        self.messages = []  # Variable for messages to UserWarning
        
    def populate_data(self, transects, compute_sensitivity=True):
        """Store data in instance variables.

        Parameters
        ----------
        transects: list
            List of transects of TransectData
        compute_sensitivity: bool
            Determines is sensitivity should be computed.
        """

        self.threshold = 20
        self.subsection = [0, 100]
        self.fit_method = 'Automatic'
        self.process_profiles(transects=transects, data_type='q')
        # Compute the sensitivity of the final discharge to changes in extrapolation methods
        if compute_sensitivity:
            self.q_sensitivity = ExtrapQSensitivity()
            self.q_sensitivity.populate_data(transects=transects, extrap_fits=self.sel_fit)

    def populate_from_qrev_mat(self, meas_struct):
        """Populates the object using data from previously saved QRev Matlab file.

        Parameters
        ----------
        meas_struct: mat_struct
           Matlab data structure obtained from sio.loadmat
        """

        if hasattr(meas_struct, 'extrapFit'):
            self.threshold = meas_struct.extrapFit.threshold
            self.subsection = meas_struct.extrapFit.subsection
            self.fit_method = meas_struct.extrapFit.fitMethod
            self.norm_data = NormData.qrev_mat_in(meas_struct.extrapFit)
            self.sel_fit = SelectFit.qrev_mat_in(meas_struct.extrapFit)
            self.q_sensitivity = ExtrapQSensitivity()
            self.q_sensitivity.populate_from_qrev_mat(meas_struct.extrapFit)
            self.messages = meas_struct.extrapFit.messages.tolist()

    def process_profiles(self, transects, data_type):
        """Function that coordinates the fitting process.

        Parameters
        ----------
        transects: TransectData
            Object of TransectData
        data_type: str
            Type of data processing (q or v)
        """

        # Compute normalized data for each transect
        self.norm_data = []
        for transect in transects:
            norm_data = NormData()
            norm_data.populate_data(transect=transect,
                                    data_type=data_type,
                                    threshold=self.threshold,
                                    data_extent=self.subsection)
            self.norm_data.append(norm_data)

        # Compute composite normalized data
        comp_data = NormData()
        comp_data.create_composite(transects=transects, norm_data=self.norm_data, threshold=self.threshold)
        self.norm_data.append(comp_data)

        # Compute the fit for the selected  method
        if self.fit_method == 'Manual':
            for n in range(len(transects)):
                self.sel_fit[n].populate_data(normalized=self.norm_data[n],
                                              fit_method=self.fit_method,
                                              top=transects[n].extrap.top_method,
                                              bot=transects[n].extrap.bot_method,
                                              exponent=transects[n].extrap.exponent)
        else:
            self.sel_fit = []
            for n in range(len(self.norm_data)):
                sel_fit = SelectFit()
                sel_fit.populate_data(self.norm_data[n], self.fit_method)
                self.sel_fit.append(sel_fit)

        if self.sel_fit[-1].top_fit_r2 is not None:
            # Evaluate if there is a potential that a 3-point top method may be appropriate
            if (self.sel_fit[-1].top_fit_r2 > 0.9 or self.sel_fit[-1].top_r2 > 0.9) \
                and np.abs(self.sel_fit[-1].top_max_diff) > 0.2:
                self.messages.append('The measurement profile may warrant a 3-point fit at the top')
                
    def update_q_sensitivity(self, transects):
        self.q_sensitivity = ExtrapQSensitivity()
        self.q_sensitivity.populate_data(transects, self.sel_fit)
        
    def change_fit_method(self, transects, new_fit_method, idx, top=None, bot=None, exponent=None, compute_qsens=True):
        """Function to change the extrapolation method"""
        self.fit_method = new_fit_method

        self.sel_fit[idx].populate_data(self.norm_data[idx], new_fit_method,  top=top, bot=bot, exponent=exponent)
        if compute_qsens & idx == len(self.norm_data)-1:
            self.q_sensitivity = ExtrapQSensitivity()
            self.q_sensitivity.populate_data(transects, self.sel_fit)
        
    def change_threshold(self, transects, data_type, threshold):
        """Function to change the threshold for accepting the increment median as valid.  The threshold
        is in percent of the median number of points in all increments"""
        
        self.threshold = threshold
        self.process_profiles(transects=transects, data_type=data_type)
        self.q_sensitivity = ExtrapQSensitivity()
        self.q_sensitivity.populate_data(transects=transects, extrap_fits=self.sel_fit)
        
    def change_extents(self, transects, data_type, extents):
        """Function allows the data to be subsection by specifying the percent cumulative discharge
        for the start and end points.  Currently this function does not consider transect direction"""
        
        self.subsection = extents
        self.process_profiles(transects=transects, data_type=data_type)
        self.q_sensitivity = ExtrapQSensitivity()
        self.q_sensitivity.populate_data(transects=transects, extrap_fits=self.sel_fit)
        
    def change_data_type(self, transects, data_type):
        self.process_profiles(transects=transects, data_type=data_type)
        self.q_sensitivity = ExtrapQSensitivity()
        self.q_sensitivity.populate_data(transects=transects, extrap_fits=self.sel_fit)

    def change_data_auto(self, transects):
        self.threshold = 20
        self.subsection = [0,100]
        self.process_profiles(transects=transects, data_type='q')
        # Compute the sensitivity of the final discharge to changes in extrapolation methods
        self.q_sensitivity = ExtrapQSensitivity()
        self.q_sensitivity.populate_data(transects=transects, extrap_fits=self.sel_fit)