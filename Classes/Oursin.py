import pandas as pd
import copy
from Classes.BoatStructure import *
from Classes.QComp import QComp
import math
from scipy.stats import t
import matplotlib.pyplot as plt


class Oursin(object):
    """Computes the uncertainty of a measurement using Oursin method.

    Attributes
    ----------
    exp_pp_min_user: float
        User provided minimum power-power exponent for simulating possible discharge
    exp_pp_max_user: float
        User provided maximum power-power exponent for simulating possible discharge
    exp_ns_min_user: float
        User provided minimum no-slip exponent for simulating possible discharge
    exp_ns_max_user: float
        User provided maximum no-slip exponent for simulating possible discharge
    draft_error_user: float
        User provided draft error (in cm) for simulating possible discharge
    d_right_error_user: float
        User provided distance error (in %) for the right edge
    d_left_error_user: float
        User provided distance error (in %) for the left edge
    u_movbed_user: float
        User provided estimate of 68% uncertainty due to moving-bed tests and conditions (in %)
    u_syst_mean_user: float
        User provided estimate of 68% uncertainty due to systematic errors (in %)
    u_cov_68_user: float
        User provided estimate of 68% uncertainty due to coefficient of variation(in %)
    u_ens_user: float
        User provided estimate of 68% uncertainty due the limited number of ensembles (in %)
    u_meas_mean_user: float
        User provided estimate of 68% uncertainty from the measured area (in %)
    u_top_mean_user: float
        User provided estimate of 68% uncertainty due the top extrapolated discharge (in %)
    u_bot_mean_user: float
        User provided estimate of 68% uncertainty due the bottom extrapolated discharge  (in %)
    u_right_mean_user: float
        User provided estimate of 68% uncertainty due the right edge discharge (in %)
    u_left_mean_user: float
        User provided estimate of 68% uncertainty due the left edge discharge (in %)
    u_badcell_user: float
        User provided estimate of 68% uncertainty due bad cells interpolation (in %)
    u_badens_user: float
        User provided estimate of 68% uncertainty due bad ensembles interpolation (in %)
    U_total_95_user: float
        User provided estimate of 95% total uncertainty (in %)

    u_prct_dzi: float
        The uncertainty related to depth cell size
    r_corr_cell: float
        The correlation between contiguous cells
    amb_vel: float
        The ambiguity velocity (m/s)
    nb_cyc: float
        the number of carrier cycles per pulse code element
        (4 or 16 when the ADCP is set up with WB0 or WB1 commands, respectively)
    r_corr_signal: float
        The correlation of the beam i in the cell j where the calculations are being done
    n_pings_wt: float
        The number of pings averaged together to obtain the water velocity estimate

    bot_meth: list
        List that contains the method proposed by Extrap for each transect
    exp_95ic_min: list
        List that contains the min range of 95% interval if power-power method is used for transect
    exp_95ic_max: list
        List that contains the max range of 95% interval if power-power method is used for transect
    pp_exp: list
        List that contains the power-power exponent computed by Extrap for Power-Power transect only
    ns_exp: list
        List that contains the no-slip exponent computed by Extrap for No-Slip method transect only

    exp_pp_min: float
        Minimum power-power exponent used for simulating possible discharge
    exp_pp_max: float
        Maximum power-power exponent used for simulating possible discharge
    exp_ns_min: float
        Minimum no-slip exponent used for simulating possible discharge
    exp_ns_max: float
        Maximum no-slip exponent used for simulating possible discharge
    d_right_error_min: list
        List that contains the minimum right distance (in m) used for simulating the discharge for each transect
    d_left_error_min: list
        List that contains the minimum left distance (in m) used for simulating the discharge for each transect
    d_right_error_max: list
        List that contains the maximum right distance (in m) used for simulating the discharge for each transect
    d_left_error_max: list
        List that contains the maximum left distance (in m) used for simulating the discharge for each transect
    list_draft_error: list
        List that contains the draft (in cm) used for simulating the discharge for each transect

    u_syst_list: list
        List that contains the computed systematic uncertainty (68%) for each transect
    u_meas_list: list
        List that contains the computed measured area uncertainty (68%) for each transect
    u_ens_list: list
       List that contains the computed uncertainty (68%) due to limited number of ensemble for each transect
    u_movbed_list: list
       List that contains the estimated uncertainty (68%) due to moving bed for each transect
    u_badens_list: list
       List that contains the computed uncertainty (68%) due to bad ensembles interpolation for each transect
    u_badcell_list: list
       List that contains the computed uncertainty (68%) due to bad cells interpolation  for each transect
    u_top_list: list
       List that contains the computed uncertainty (68%) due to top discharge extrapolation for each transect
    u_bot_list: list
       List that contains the computed uncertainty (68%) due to bottom discharge extrapolation for each transect
    u_left_list: list
       List that contains the computed uncertainty (68%) due to left discharge extrapolation for each transect
    u_right_list: list
       List that contains the computed uncertainty (68%) due to right discharge extrapolation for each transect
    cov_68 =  None
       Computed uncertainty (68%) due to coefficient of variation

    u_contrib_meas_v_boat: list
        Relative contribution (in %) of v_boat uncertainty to the measured uncertainty for each transect
    u_contrib_errv_v_boat: list
        Relative contribution (in %) of v_boat error velocity to the measured uncertainty for each transect
    u_contrib_verv_h_depth: list
       Relative contribution (in %) of v_boat vertical velocity to the measured uncertainty for each transect
    u_contrib_errv_v_wate: list
       Relative contribution (in %) of v_water error velocity to the measured uncertainty for each transect
    u_contrib_meas_v_wate: list
       Relative contribution (in %) of v_water uncertainty to the measured uncertainty for each transect
    u_contrib_meas_u_dzi : list
       Relative contribution (in %) of depth cell uncertainty to the measured uncertainty for each transect

    # --- Relative uncertainty
    u_syst_mean: float
        Systematic uncertainty (68%) used for the measurement
    u_combined_by_transect: list
        List that contains the combined uncertainty (68%) for each transect
    u_terms: list
        List of computed uncertainty terms for the measurement
    contrib_terms_total: list
        List of contribution of each terms to the total uncertainty
    contrib_legend: list
        List of term labels associated with u_terms and contrib_terms_total
    u_combined_total: float
        Combined uncertainty (68%) for the measurement
    U_total_by_transect: list
        List that contains the total combined uncertainty (95%) for each transect
    U_total_95: float
        Total uncertainty (95%) for the measurement
    variance_terms_by_transect: DataFrame
        Variance (68%²) for each term and for each transect


    # -- Absolute uncertainty (in m3/s or variance in m6/s2)
    u_syst_mean_abs: float
        Systematic uncertainty (68%) used for the measurement
    u_combined_by_transect_abs: list
        List that contains the combined uncertainty (68%) for each transect
    u_terms_abs: list
        List of computed uncertainty terms for the measurement
    u_combined_total_abs: float
        Combined uncertainty (68%) for the measurement
    U_total_by_transect_abs: list
        List that contains the total combined uncertainty (95%) for each transect
    U_total_95_abs: float
        Total uncertainty (95%) for the measurement
    variance_terms_by_transect_abs: DataFrame
        Variance (68% m6/s2) for each term and for each transect


    nb_transects: float
        Number of transects used

    # --- Store results of all simulations in DataFrame
    simu1: DataFrame
        Discharges (total, and subareas) computed for simulation 1
    simu2: DataFrame
        Discharges (total, and subareas) computed for simulation 2
    simu3: DataFrame
        Discharges (total, and subareas) computed for simulation 3
    simu3min: DataFrame
        Discharges (total, and subareas) computed for simulation 3min
    simu3max: DataFrame
        Discharges (total, and subareas) computed for simulation 3max
    simu4: DataFrame
        Discharges (total, and subareas) computed for simulation 4
    simu5: DataFrame
        Discharges (total, and subareas) computed for simulation 5
    simu5min: DataFrame
        Discharges (total, and subareas) computed for simulation 5min
    simu5max: DataFrame
        Discharges (total, and subareas) computed for simulation 5max
    simu6: DataFrame
        Discharges (total, and subareas) computed for simulation 6
    simu7: DataFrame
        Discharges (total, and subareas) computed for simulation 7
    simu8: DataFrame # not used
        Discharges (total, and subareas) computed for simulation 8
    simu9: DataFrame # edge
        Discharges (total, and subareas) computed for simulation 9
    simu10: DataFrame # edge
        Discharges (total, and subareas) computed for simulation 10
    simu11: DataFrame # draft
        Discharges (total, and subareas) computed for simulation 11
    simu12: DataFrame # draft
        Discharges (total, and subareas) computed for simulation 12
    simu13: DataFrame # missing ens
        Discharges (total, and subareas) computed for simulation 13
    simu14: DataFrame # missing ens
        Discharges (total, and subareas) computed for simulation 14
    simu15: DataFrame # missing ens
        Discharges (total, and subareas) computed for simulation 15
    simu16: DataFrame
        Discharges (total, and subareas) computed for simulation 16
    simu17: DataFrame
        Discharges (total, and subareas) computed for simulation 17
    simu18: DataFrame # missing cells
        Discharges (total, and subareas) computed for simulation 18
    simu19: DataFrame # missing cells
        Discharges (total, and subareas) computed for simulation 19
    simu20: DataFrame # missing cells
        Discharges (total, and subareas) computed for simulation 20
    simu21: DataFrame # missing cells
        Discharges (total, and subareas) computed for simulation 21
    simu22: DataFrame # missing cells
        Discharges (total, and subareas) computed for simulation 22
    simu23: DataFrame # missing cells
        Discharges (total, and subareas) computed for simulation 23
    simu24: DataFrame # missing cells
        Discharges (total, and subareas) computed for simulation 24
    simu25: DataFrame # missing cells
        Discharges (total, and subareas) computed for simulation 25

    Simu_checked: Dict
        Dict that shows which simulation are used to compute the uncertainty
    Simu_checked_user: Dict
        User provided dict for selecting which simulation to be used to compute the uncertainty
    Simu_dischage: Dict
        Dict that gathers all simulations
    """

    def __init__(self):
        """Initialize class and instance variables."""

        # User provided parameters
        self.exp_pp_min_user = None  # float
        self.exp_pp_max_user = None
        self.exp_ns_min_user = None
        self.exp_ns_max_user = None
        self.draft_error_user = None  # [cm]
        self.d_right_error_user = None  # [m]
        self.d_left_error_user = None  # [m]
        self.u_movbed_user = None  # [%] moving bed uncertainty at 68% ex: 1.5
        self.u_syst_mean_user = None  # [%] systematic uncertainty at 68% ex: 1.5
        self.u_cov_68_user = None  # [%]
        self.u_ens_user = None  # [%]
        self.u_meas_mean_user = None  # [%]
        self.u_top_mean_user = None  # [%]
        self.u_bot_mean_user = None  # [%]
        self.u_right_mean_user = None  # [%]
        self.u_left_mean_user = None  # [%]
        self.u_badcell_user = None  # [%]
        self.u_badens_user = None  # [%]
        self.U_total_95_user = None
        self.u_prct_dzi = None
        self.r_corr_cell = None
        self.amb_vel = None
        self.nb_cyc = None
        self.r_corr_signal = None
        self.n_pings_wt = None

        # Extrap results
        self.bot_meth = []
        self.exp_95ic_min = []
        self.exp_95ic_max = []
        self.pp_exp = []
        self.ns_exp = []

        # Parameters used for computing the uncertainty
        self.exp_pp_min = None  # float Min power-power exponent (between 0 and 1)
        self.exp_pp_max = None  # float Max power-power exponent (between 0 and 1)
        self.exp_ns_min = None  # float Min no-slip exponent (between 0 and 1)
        self.exp_ns_max = None  # float Max no-Slip  exponent (between 0 and 1)
        self.d_right_error_min = []  # list of min distance for right edge
        self.d_left_error_min = []  # list of max distance for right edge
        self.d_right_error_max = []  # list of min distance for left edge
        self.d_left_error_max = []  # list of max distance for left edge
        self.list_draft_error = []  # store draft error in a list

        # Terms computed by transects (list at 68% level)
        self.u_syst_list = []
        self.u_meas_list = []
        self.u_ens_list = []
        self.u_movbed_list = []
        self.u_badens_list = []
        self.u_badcell_list = []
        self.u_top_list = []
        self.u_bot_list = []
        self.u_left_list = []
        self.u_right_list = []
        self.cov_68 = None

        # Relative contribution of each component to the measured uncertainty
        self.u_contrib_meas_v_boat = []
        self.u_contrib_errv_v_boat = []
        self.u_contrib_verv_h_depth = []
        self.u_contrib_errv_v_wate = []
        self.u_contrib_meas_v_wate = []
        self.u_contrib_meas_u_dzi = []

        # Overall measurement average
        self.u_syst_mean = None
        self.u_combined_by_transect = []
        self.U_total_by_transect = []
        self.u_terms = []
        self.u_combined_total = None
        self.U_total_95 = None
        self.variance_terms_by_transect = pd.DataFrame()
        self.contrib_terms_total = []
        self.contrib_legend = []
        self.nb_transects = None

        # Absolute uncertainties
        self.u_syst_mean_abs = None
        self.u_combined_by_transect_abs = []
        self.u_terms_abs = []
        self.u_combined_total_abs = []
        self.U_total_by_transect_abs = []
        self.U_total_95_abs = None
        self.variance_terms_by_transect_abs = pd.DataFrame()

        # --- Store results of all simulations in DataFrame
        self.simu1 = pd.DataFrame()
        self.simu2 = pd.DataFrame()
        self.simu3 = pd.DataFrame()
        self.simu3min = pd.DataFrame()
        self.simu3max = pd.DataFrame()
        self.simu4 = pd.DataFrame()
        self.simu5 = pd.DataFrame()
        self.simu5min = pd.DataFrame()
        self.simu5max = pd.DataFrame()
        self.simu6 = pd.DataFrame()
        self.simu7 = pd.DataFrame()
        self.simu8 = pd.DataFrame()  # not used
        self.simu9 = pd.DataFrame()  # edge
        self.simu10 = pd.DataFrame()  # edge
        self.simu11 = pd.DataFrame()  # draft
        self.simu12 = pd.DataFrame()  # draft
        self.simu13 = pd.DataFrame()  # missing ens
        self.simu14 = pd.DataFrame()  # missing ens
        self.simu15 = pd.DataFrame()  # missing ens
        self.simu16 = pd.DataFrame()
        self.simu17 = pd.DataFrame()
        self.simu18 = pd.DataFrame()  # missing cells
        self.simu19 = pd.DataFrame()  # missing cells
        self.simu20 = pd.DataFrame()  # missing cells
        self.simu21 = pd.DataFrame()  # missing cells
        self.simu22 = pd.DataFrame()  # missing cells
        self.simu23 = pd.DataFrame()  # missing cells
        self.simu24 = pd.DataFrame()  # missing cells
        self.simu25 = pd.DataFrame()  # missing cells

        # Simulation used or not
        self.Simu_checked = dict()
        self.Simu_checked_user = dict()
        self.Simu_dischage = dict()

    def compute_oursin(self, meas,
                       exp_pp_min_user=None,
                       exp_pp_max_user=None,
                       exp_ns_min_user=None,
                       exp_ns_max_user=None,
                       draft_error_user=None,
                       d_right_error_prct_user=None,
                       d_left_error_prct_user=None,
                       u_syst_mean_user=None,
                       u_movbed_user=None,
                       u_meas_mean_user=None,
                       u_cov_68_user=None,
                       u_ens_user=None,
                       u_top_mean_user=None,
                       u_bot_mean_user=None,
                       u_right_mean_user=None,
                       u_left_mean_user=None,
                       u_badcell_user=None,
                       u_badens_user=None,
                       U_total_95_user=None,
                       Simu_checked_user=None,
                       u_prct_dzi_user=None,
                       r_corr_cell_user=None,
                       amb_vel_user=None,
                       nb_cyc_user=None,
                       r_corr_signal_user=None,
                       n_pings_wt_user=None
                       ):
        """Computes the uncertainty for the components of the discharge measurement
        using measurement data or user provided values.

        Parameters
        ----------
        meas: Measurement
            Object of class Measurement
        exp_pp_min_user: float
            User provided minimum power-power exponent for simulating possible discharge
        exp_pp_max_user: float
            User provided maximum power-power exponent for simulating possible discharge
        exp_ns_min_user: float
            User provided minimum no-slip exponent for simulating possible discharge
        exp_ns_max_user: float
            User provided maximum no-slip exponent for simulating possible discharge
        draft_error_user: float
            User provided draft error (in cm) for simulating possible discharge
        d_right_error_prct_user: float
            User provided distance error (in %) for the right edge
        d_left_error_prct_user: float
            User provided distance error (in %) for the left edge
        u_syst_mean_user: float
            User provided estimate of 68% uncertainty due to systematic errors (in %)
        u_movbed_user: float
            User provided estimate of 68% uncertainty due to moving-bed tests and conditions (in %)
        u_meas_mean_user: float
            User provided estimate of 68% uncertainty from the measured area (in %)
        u_cov_68_user: float
            User provided estimate of 68% uncertainty due to coefficient of variation(in %)
        u_ens_user: float
            User provided estimate of 68% uncertainty due the limited number of ensembles (in %)
        u_top_mean_user: float
            User provided estimate of 68% uncertainty due the top extrapolated discharge (in %)
        u_bot_mean_user: float
            User provided estimate of 68% uncertainty due the bottom extrapolated discharge  (in %)
        u_right_mean_user: float
            User provided estimate of 68% uncertainty due the right edge discharge (in %)
        u_left_mean_user: float
            User provided estimate of 68% uncertainty due the left edge discharge (in %)
        u_badcell_user: float
            User provided estimate of 68% uncertainty due bad cells interpolation (in %)
        u_badens_user: float
            User provided estimate of 68% uncertainty due bad ensembles interpolation (in %)
        U_total_95_user: float
            User provided estimate of 95% total uncertainty (in %)
        Simu_checked_user: Dict
            User provided dict for selecting which simulation to be used to compute the uncertainty
        u_prct_dzi_user: float
            User provided uncertainty related to depth cell size
        r_corr_cell_user: float
            User provided correlation between contiguous cells
        amb_vel_user: float
            User provided ambiguity velocity (m/s)
        nb_cyc_user: float
            User provided number of carrier cycles per pulse code element
            (4 or 16 when the ADCP is set up with WB0 or WB1 commands, respectively)
        r_corr_signal_user: float
            User provided correlation of the beam i in the cell j where the calculations are being done
        n_pings_wt_user: float
            User provided number of pings averaged together to obtain the water velocity estimate
        """

        # Use only checked discharges
        # Extract discharges and other data that are used later on (PP and NS exponents)
        # Compute the uncertainty related to the limited number of ensembles (ISO 748)
        checked = []
        discharges = []
        total_q = []

        if Simu_checked_user is None:
            Simu_checked_user = dict()

        # Get discharges and extrapolation data for each transect
        for n in range(len(meas.transects)):
            checked.append(meas.transects[n].checked)
            if meas.transects[n].checked:
                discharges.append(meas.discharge[n])
                total_q.append(meas.discharge[n].total)

                # TODO Seems this would be better placed somewhere else
                # Compute uncertainty due to limited number of ensembles (ISO 748; Le Coz et al., 2012)
                self.u_ens_list.append(0.01 * 32 * len(meas.discharge[n].middle_ens) ** (-0.88))

                # Bottom method selected using data from each transect only
                self.bot_meth.append(meas.extrap_fit.sel_fit[n].bot_method_auto)

                # Store 95 percent bounds on power fit exponent for each transect if power selected
                if meas.extrap_fit.sel_fit[n].bot_method_auto == "Power":
                    if np.isnan(meas.extrap_fit.sel_fit[0].exponent_95_ci[0]):
                        self.exp_95ic_min.append(np.nan)
                    else:
                        self.exp_95ic_min.append(meas.extrap_fit.sel_fit[n].exponent_95_ci[0][0])

                    if np.isnan(meas.extrap_fit.sel_fit[0].exponent_95_ci[1]):
                        self.exp_95ic_max.append(np.nan)
                    else:
                        self.exp_95ic_max.append(meas.extrap_fit.sel_fit[n].exponent_95_ci[1][0])

                    self.pp_exp.append(meas.extrap_fit.sel_fit[n].pp_exponent)

                # Store no slip exponent if no slip selected
                elif meas.extrap_fit.sel_fit[n].bot_method_auto == "No Slip":
                    self.ns_exp.append(meas.extrap_fit.sel_fit[n].ns_exponent)

        self.nb_transects = len(discharges)
        # print(self.exp_95ic_min)

        # 1. Systematic terms + correction terms (moving bed)
        #   1.a. Moving-bed / Same than QRev or user override
        if u_movbed_user is None:
            u_movbed_68 = self.compute_moving_bed_uncertainty(meas)
        else:
            # TODO Why is u_movbed_user stored as % rather than % * 0.01
            self.u_movbed_user = u_movbed_user
            u_movbed_68 = 0.01 * u_movbed_user

        self.u_movbed_list = [u_movbed_68] * self.nb_transects

        #   1.b.  Systematic. Use 1.31% or user override
        if u_syst_mean_user is None:
            self.u_syst_mean = self.compute_systematic_uncertainty()
        else:
            self.u_syst_mean_user = u_syst_mean_user  # Store the value if not None
            self.u_syst_mean = u_syst_mean_user * 0.01

        self.u_syst_list = [self.u_syst_mean] * self.nb_transects  # Repeated to be applied to each transect

        # 2. Measured uncertainty
        #   2.a. Measured area BY EQUATION
        # Standard relative uncertainty of depth cell size 0.5% or user override
        self.measured_area_uncertainty(u_prct_dzi_user=u_prct_dzi_user,
                                       r_corr_cell_user=r_corr_cell_user,
                                       amb_vel_user=amb_vel_user,
                                       nb_cyc_user=nb_cyc_user,
                                       r_corr_signal_user=r_corr_signal_user,
                                       n_pings_wt_user=n_pings_wt_user)

        #   2.b. Coefficient of variation (same as QRev but 68% level of confidence) or user override
        # TODO COV stored as % not % * 0.01
        if u_cov_68_user is None:
            self.cov_68 = self.compute_meas_cov(meas)
        else:
            self.u_cov_68_user = u_cov_68_user  # Store the value if not None
            self.cov_68 = u_cov_68_user

        # 3. Run all the simulations to compute possible discharges
        self.run_oursin_simulations(meas,exp_pp_min_user,exp_pp_max_user,exp_ns_min_user,exp_ns_max_user,
                                    draft_error_user,d_right_error_prct_user,d_left_error_prct_user)

        self.Simu_dischage = dict({
            'simu1': self.simu1,
            'simu2': self.simu2,
            'simu3': self.simu3,
            'simu3min': self.simu3min,
            'simu3max': self.simu3max,
            'simu4': self.simu4,
            'simu5': self.simu5,
            'simu5min': self.simu5min,
            'simu5max': self.simu5max,
            'simu6': self.simu6,
            'simu7': self.simu7,
            'simu8': self.simu8,
            'simu9': self.simu9,
            'simu10': self.simu10,
            'simu11': self.simu11,
            'simu12': self.simu12,
            'simu13': self.simu13,
            'simu14': self.simu14,
            'simu15': self.simu15,
            'simu16': self.simu16,
            'simu17': self.simu17,
            'simu18': self.simu18,
            'simu19': self.simu19,
            'simu20': self.simu20,
            'simu21': self.simu21,
            'simu22': self.simu22,
            'simu23': self.simu23,
            'simu24': self.simu24,
            'simu25': self.simu25,
        })

        # 4. Active or inactive simulations
        if not bool(Simu_checked_user): # if the dict is empty, then use default
            self.Simu_checked = dict({
                'simu1': True,
                'simu2': True,
                'simu3': True,
                'simu3min': True,
                'simu3max': True,
                'simu4': True,
                'simu5': True,
                'simu5min': True,
                'simu5max': True,
                'simu6': True,
                'simu7': True,
                'simu8': False,  # Not computed
                'simu9': True,
                'simu10': True,
                'simu11': True,
                'simu12': True,
                'simu13': True,
                'simu14': True,
                'simu15': False,  # Not computed
                'simu16': False,  # Not computed
                'simu17': False,  # Not computed
                'simu18': True,
                'simu19': True,
                'simu20': True,
                'simu21': False,  # Not computed
                'simu22': True,
                'simu23': True,
                'simu24': False,  # Not computed
                'simu25': False,  # Not computed
            })


        else:
            self.Simu_checked_user = Simu_checked_user
            self.Simu_checked = Simu_checked_user

        # Replace inactivated simulations by simu1
        for (key, value) in self.Simu_checked.items():
            # Check if any simulation is unchecked then replace it by simu1
            if value == False:
                self.Simu_dischage[key] = self.simu1

        # 5. Compute terms based on possible simulations and assuming a rectangular law
        self.u_badens_list = Oursin.apply_u_rect([self.Simu_dischage['simu1']['q_total'],
                                                  self.Simu_dischage['simu13']['q_total'],
                                                  self.Simu_dischage['simu14']['q_total']]) \
                             / self.simu1['q_total']
        self.u_badcell_list =  Oursin.apply_u_rect([self.Simu_dischage['simu1']['q_total'],
                                                    self.Simu_dischage['simu18']['q_total'],
                                                    self.Simu_dischage['simu19']['q_total'],
                                                    self.Simu_dischage['simu20']['q_total'],
                                                    self.Simu_dischage['simu22']['q_total'],
                                                    self.Simu_dischage['simu23']['q_total']]) \
                              / self.simu1['q_total']

        self.u_top_list = Oursin.apply_u_rect([self.Simu_dischage['simu1']['q_top'],
                                                 self.Simu_dischage['simu3']['q_top'],
                                                 self.Simu_dischage['simu3min']['q_top'],
                                                 self.Simu_dischage['simu3max']['q_top'],
                                                 self.Simu_dischage['simu5']['q_top'],
                                                 self.Simu_dischage['simu5min']['q_top'],
                                                 self.Simu_dischage['simu5max']['q_top'],
                                                 self.Simu_dischage['simu7']['q_top'],
                                                 self.Simu_dischage['simu11']['q_top'],
                                                 self.Simu_dischage['simu12']['q_top']]) \
                          / self.simu1['q_total']

        self.u_bot_list = Oursin.apply_u_rect([self.simu1['q_bot'],
                                                 self.Simu_dischage['simu3']['q_bot'],
                                                 self.Simu_dischage['simu3min']['q_bot'],
                                                 self.Simu_dischage['simu3max']['q_bot'],
                                                 self.Simu_dischage['simu5']['q_bot'],
                                                 self.Simu_dischage['simu5min']['q_bot'],
                                                 self.Simu_dischage['simu5max']['q_bot'],
                                                 self.Simu_dischage['simu7']['q_bot']]) \
                          / self.simu1['q_total']

        self.u_left_list = Oursin.apply_u_rect([self.simu1['q_left'],
                                                  self.Simu_dischage['simu9']['q_left'],
                                                  self.Simu_dischage['simu10']['q_left'],
                                                  self.Simu_dischage['simu11']['q_left'],
                                                  self.Simu_dischage['simu12']['q_left']]) \
                           / self.simu1['q_total']

        self.u_right_list = Oursin.apply_u_rect([self.simu1['q_right'],
                                                  self.Simu_dischage['simu9']['q_right'],
                                                  self.Simu_dischage['simu10']['q_right'],
                                                  self.Simu_dischage['simu11']['q_right'],
                                                  self.Simu_dischage['simu12']['q_right']]) \
                           / self.simu1['q_total']

        # Use user-provided values
        if u_badens_user is not None:
            self.u_badens_list = [0.01 * u_badens_user]*len(discharges)
            self.u_badens_user=u_badens_user
        if u_badcell_user is not None:
            self.u_badcell_list = [0.01 * u_badcell_user]*len(discharges)
            self.u_badcell_user=u_badcell_user
        if u_top_mean_user is not None:
            self.u_top_list = [0.01 * u_top_mean_user]*len(discharges)
            self.u_top_mean_user=u_top_mean_user
        if u_bot_mean_user is not None:
            self.u_bot_list = [0.01 * u_bot_mean_user]*len(discharges)
            self.u_bot_mean_user=u_bot_mean_user
        if u_left_mean_user is not None:
            self.u_left_list = [0.01 * u_left_mean_user]*len(discharges)
            self.u_left_mean_user=u_left_mean_user
        if u_right_mean_user is not None:
            self.u_right_list = [0.01 * u_right_mean_user]*len(discharges)
            self.u_right_mean_user=u_right_mean_user
        if u_meas_mean_user is not None:
            self.u_meas_list = [0.01 * u_meas_mean_user]*len(discharges)
            self.u_meas_mean_user=u_meas_mean_user
        if u_ens_user is not None:
            self.u_ens_user = u_ens_user
            self.u_ens_list = [0.01 * u_ens_user]*len(discharges)

        # 6. Combined by transects and contribution
        #    Evaluate the coefficient of variation and add it if cov²>oursin²
        self.compute_combined_uncertainty()

        # Use user provided uncertainty
        if U_total_95_user is not None:
            self.U_total_95 = U_total_95_user
            self.U_total_95_user = U_total_95_user

    def u_meas_compute(self ,meas, u_prct_dzi = 0.005, r_corr = 1, V_a = 0.5, Cyc = 4, R_corr = 0.8, n_pings_wt = 1):
        """
        Compute the uncertainty related to the measured area
        (boat and water velocity, depth cell uncertainty)

        Parameters
        ----------
        :param meas: Measurement
            Object of class Measurement
        :param u_prct_dzi: float
            Uncertainty (68%) related to the depth cell size - Default is 0.005 * 0.01 # k=1 0.5%
        :param r_corr: float
            Correlation between errors of contiguous cells. Should be included between 0 and 1.
             Default is 1 assuming a maximum correlation
        :param V_a: float
            Ambiguity velocity. Default is 0.50 m/s
        :param Cyc: float
            The number of carrier cycles per pulse code element
            (4 or 16 when the ADCP is set up with WB0 or WB1 commands, respectively)
            Default is 4
        :param R_corr: float
            Correlation of the signal. Correlation of the beam i in the cell j where
             the calculations are being done. Default is 0.80
        :param n_pings_wt: float (integer)
            The number of pings averaged together to obtain the velocity estimate
            Random error in successive pings are uncorrelated. Mximum uncertainty is when default value is set to 1

        :return: u_meas_list: list of measured uncertainty (68%) for each transect and contribution
        of each terms to the measured uncertainty (u_contrib_meas_v_boat, u_contrib_errv_v_boat, u_contrib_verv_h_depth,
        u_contrib_errv_v_wate, u_contrib_meas_v_wate, u_contrib_meas_u_dzi).
        """

        # Initializes the lists
        u_meas_list =  []
        u_contrib_meas_v_boat =  []
        u_contrib_errv_v_boat =  []
        u_contrib_verv_h_depth =  []
        u_contrib_errv_v_wate =  []
        u_contrib_meas_v_wate =  []
        u_contrib_meas_u_dzi =  []

        # ind_checked = [x for x in range(len(meas.transects)) if meas.transects[x].checked==1]
        for ind_transect in range(self.nb_transects):
        # for ind_transect in range(len(meas.transects)):
            if meas.transects[ind_transect].checked == 1:

                # -----Relative depth error due to vertical velocity of boat
                relative_error_depth = self.depth_error_boat_motion(meas.transects[ind_transect])

                # ----- Computation of theoretical relative standard deviation of boat velocity (Shaw and Brumley 1993)
                u_prct_v_boatm_ens = self.boat_std_by_equation(meas.transects[ind_transect])

                # -----Computation of theoretical standard deviation of water velocity (RDI 1996) BroadBand
                u_prct_v_water_ens = self.water_std_by_equation(transect=meas.transects[ind_transect],
                                                                V_a=V_a,
                                                                Cyc=Cyc,
                                                                R_corr=R_corr,
                                                                n_pings_wt=n_pings_wt)

                # ------ Relative standard deviation of error velocity (Water Track)
                std_ev_WT_ens = self.water_std_by_error_velocity(meas.transects[ind_transect])

                # ------ Relative standard deviation of error velocity (Bottom Track)
                std_ev_BT = self.boat_std_by_error_velocity(meas.transects[ind_transect])

                # ----- Computation of u_meas
                Q_2_tran = meas.discharge[ind_transect].total ** 2
                q_2_ens = meas.discharge[ind_transect].middle_ens ** 2
                n_cell_ens = meas.transects[ind_transect].w_vel.cells_above_sl.sum(axis=0)  # number of cells by ens
                n_cell_ens = np.where(n_cell_ens == 0, np.nan, n_cell_ens)

                # ----- Variance for each ensembles
                u_2_meas = q_2_ens * (u_prct_v_boatm_ens ** 2 +
                                      relative_error_depth **2 +
                                      std_ev_BT ** 2 +
                                      (1 / n_cell_ens) * (std_ev_WT_ens ** 2 +
                                                          u_prct_v_water_ens ** 2 +
                                                          u_prct_v_water_ens ** 2 * r_corr * (n_cell_ens - 1) +
                                                          u_prct_dzi ** 2))
                # TODO DSM I would have computed as follows
                # u_2_meas = q_2_ens * (u_prct_dzi ** 2) * (std_ev_BT ** 2 + (1 / n_cell_ens) * (std_ev_WT_ens ** 2))
                u_2_meas = np.nan_to_num(u_2_meas)
                u_2_prct_meas = u_2_meas.sum() / Q_2_tran

                # ----- Standard deviation
                u_prct_meas = u_2_prct_meas ** 0.5
                u_meas_list.append(u_prct_meas)

                # Compute the contribution of all terms to u_meas (sum of a0 to g0 =1)
                a0 = (np.nan_to_num(q_2_ens * (u_prct_v_boatm_ens ** 2)).sum() / Q_2_tran) / u_2_prct_meas
                b0 = (np.nan_to_num(q_2_ens * (std_ev_BT ** 2)).sum() / Q_2_tran) / u_2_prct_meas
                c0 = (np.nan_to_num(q_2_ens * (relative_error_depth ** 2)).sum() / Q_2_tran) / u_2_prct_meas
                d0 = (np.nan_to_num(q_2_ens * ((1 / n_cell_ens) * (
                        u_prct_v_water_ens ** 2 + u_prct_v_water_ens ** 2 * r_corr * (
                        n_cell_ens - 1)))).sum() / Q_2_tran) / u_2_prct_meas
                e0 = (np.nan_to_num(q_2_ens * ((1 / n_cell_ens) * (std_ev_WT_ens ** 2))).sum() / Q_2_tran) / u_2_prct_meas
                g0 = (np.nan_to_num(q_2_ens * ((1 / n_cell_ens) * (u_prct_dzi ** 2))).sum() / Q_2_tran) / u_2_prct_meas

                u_contrib_meas_v_boat.append(a0)
                u_contrib_errv_v_boat.append(b0)
                u_contrib_verv_h_depth.append(c0)
                u_contrib_errv_v_wate.append(e0)
                u_contrib_meas_v_wate.append(d0)
                u_contrib_meas_u_dzi.append(g0)

        self.u_meas_list = u_meas_list
        self.u_contrib_meas_v_boat = u_contrib_meas_v_boat
        self.u_contrib_errv_v_boat =  u_contrib_errv_v_boat
        self.u_contrib_verv_h_depth =  u_contrib_verv_h_depth
        self.u_contrib_errv_v_wate =  u_contrib_errv_v_wate
        self.u_contrib_meas_v_wate =  u_contrib_meas_v_wate
        self.u_contrib_meas_u_dzi =  u_contrib_meas_u_dzi


    def run_oursin_simulations(self,meas,exp_pp_min_user,exp_pp_max_user,exp_ns_min_user,exp_ns_max_user,
                               draft_error_user,d_right_error_prct_user,d_left_error_prct_user):
        """Compute discharges (top, bot, right, left, total, middle)
        based on possible scenarios

        Parameters
        ----------
        meas: Measurement
            Object of class Measurement
        exp_pp_min_user: float
            User provided minimum power-power exponent for simulating possible discharge
        exp_pp_max_user: float
            User provided maximum power-power exponent for simulating possible discharge
        exp_ns_min_user: float
            User provided minimum no-slip exponent for simulating possible discharge
        exp_ns_max_user: float
            User provided maximum no-slip exponent for simulating possible discharge
        draft_error_user: float
            User provided draft error (in cm) for simulating possible discharge
        d_right_error_user: float
            User provided distance error (in %) for the right edge
        d_left_error_user: float
            User provided distance error (in %) for the left edge
        """

        # Simulation 1 is the actual reference (selected measurements) / see 2nd loop below
        q_total_1 = []
        q_top_1 = []
        q_bot_1 = []
        q_right_1 = []
        q_left_1 = []
        q_middle_1 = []

        # If list have not be saved recompute q_sensitivity
        if not hasattr(meas.extrap_fit.q_sensitivity, 'q_pp_list'):
            meas.extrap_fit.q_sensitivity.populate_data(meas.transects, meas.extrap_fit.sel_fit)

        # Simulation 2 default 1/6 power power law (already computed in ExtrapQSensitivity class)
        self.simu2['q_total'] = meas.extrap_fit.q_sensitivity.q_pp_list
        self.simu2['q_top'] = meas.extrap_fit.q_sensitivity.q_top_pp_list
        self.simu2['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_pp_list

        # Simulation 3 optimized power power law (in ExtrapQSensitivity class)
        self.simu3['q_total'] = meas.extrap_fit.q_sensitivity.q_pp_opt_list
        self.simu3['q_top'] = meas.extrap_fit.q_sensitivity.q_top_pp_opt_list
        self.simu3['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_pp_opt_list

        # Simulation 4 default 1/6 cns law (in ExtrapQSensitivity class)
        self.simu4['q_total'] = meas.extrap_fit.q_sensitivity.q_cns_list
        self.simu4['q_top'] = meas.extrap_fit.q_sensitivity.q_top_cns_list
        self.simu4['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_cns_list

        # Simulation 5 optimized cns law (ExtrapQSensitivity class)
        self.simu5['q_total'] = meas.extrap_fit.q_sensitivity.q_cns_opt_list
        self.simu5['q_top'] = meas.extrap_fit.q_sensitivity.q_top_cns_opt_list
        self.simu5['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_cns_opt_list

        # Simulation 6 default 1/6 3pt no slip law (already computed in ExtrapQSensitivity class
        self.simu6['q_total'] = meas.extrap_fit.q_sensitivity.q_3p_ns_list
        self.simu6['q_top'] = meas.extrap_fit.q_sensitivity.q_top_3p_ns_list
        self.simu6['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_3p_ns_list

        # Simulation 7 default optimized 3pt no slip law (already computed in ExtrapQSensitivity class
        self.simu7['q_total'] = meas.extrap_fit.q_sensitivity.q_3p_ns_opt_list
        self.simu7['q_top'] = meas.extrap_fit.q_sensitivity.q_top_3p_ns_opt_list
        self.simu7['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_3p_ns_opt_list

        # Other simulations based on automatically parameters or user parameters
        # Extrapolations Simu 3min-max and 5min-max
        # Intitialization
        list_draft_error = []
        q_total_3min = []
        q_top_3min = []
        q_bot_3min = []
        q_total_3max = []
        q_top_3max = []
        q_bot_3max = []
        q_total_5min = []
        q_top_5min = []
        q_bot_5min = []
        q_total_5max = []
        q_top_5max = []
        q_bot_5max = []

        # Extracted PP and NS exponents
        exp_95ic_min = self.exp_95ic_min
        exp_95ic_max = self.exp_95ic_max
        pp_exp = self.pp_exp
        ns_exp = self.ns_exp

        # Compute min-max no slip exponent
        skip_NS_min_max = False
        if len(ns_exp) == 0:
            skip_NS_min_max = True
            min_ns = meas.extrap_fit.q_sensitivity.ns_exp
            max_ns = meas.extrap_fit.q_sensitivity.ns_exp
        else:
            mean_ns = np.nanmean(ns_exp)
            if len(ns_exp) == 1:
                min_ns = ns_exp[0]-0.05
                max_ns = ns_exp[0]+0.05
            else:
                min_ns = np.nanmin(ns_exp)
                max_ns = np.nanmax(ns_exp)

            # Diff between mean NS exponent and min/max shouldn't be > 0.2
            if mean_ns - min_ns > 0.2:
                min_ns = mean_ns - 0.2
            if max_ns - mean_ns > 0.2:
                max_ns = mean_ns + 0.2

            # Check that 0 < exponent < 1
            if min_ns <= 0:
                min_ns = 0.01
            if max_ns >= 1:
                max_ns = 0.99

        # Apply user overides
        if exp_ns_min_user is None:
            exp_ns_min = min_ns
        else:
            exp_ns_min = exp_ns_min_user

        if exp_ns_max_user is None:
            exp_ns_max = max_ns
        else:
            exp_ns_max = exp_ns_max_user

        self.exp_ns_min=exp_ns_min
        self.exp_ns_max=exp_ns_max

        # Compute min-max power exponent
        skip_PP_min_max = False
        if len(pp_exp) == 0:
            skip_PP_min_max = True
            min_pp = meas.extrap_fit.q_sensitivity.pp_exp
            max_pp = meas.extrap_fit.q_sensitivity.pp_exp
        else:
            if np.isnan(pp_exp).any():
                mean_pp = 0.16
            else:
                mean_pp = np.nanmean(pp_exp)

            # If all transects have confidence intervals, use the mean of the confidence interval min/max
            # Otherwise adjust average +/- 0.2
            if np.isnan(exp_95ic_min).any():
                min_pp = mean_pp - 0.2
            else:
                min_pp = np.nanmean(exp_95ic_min)

            if np.isnan(exp_95ic_max).any():
                max_pp = mean_pp + 0.2
            else:
                max_pp = np.nanmean(exp_95ic_max)

            # Diff between mean PP exponent and min/max
            if mean_pp - min_pp > 0.2:
                min_pp = mean_pp - 0.2
            if max_pp - mean_pp > 0.2:
                max_pp = mean_pp + 0.2

            # Check that 0 < exponent < 1
            if min_pp <= 0:
                min_pp = 0.01
            if max_pp >= 1:
                max_pp = 0.99

        # Set min-max exponents of user override
        if exp_pp_min_user is None:
            exp_pp_min = min_pp
        else:
            exp_pp_min = exp_pp_min_user

        if exp_pp_max_user is None:
            exp_pp_max = max_pp
        else:
            exp_pp_max = exp_pp_max_user

        self.exp_pp_min=exp_pp_min
        self.exp_pp_max=exp_pp_max

        # Deep copy of actual measurement 'meas'
        simdraftmin_9 = copy.deepcopy(meas) # draft - error
        simdraftmax_10 = copy.deepcopy(meas) # draft + error
        simedgemin_11 = copy.deepcopy(meas) # triangular shape - error
        simedgemax_12 = copy.deepcopy(meas) # rectangular shape + error
        simbadens_last_13 = copy.deepcopy(meas) # last ens use
        simbadens_next_14 = copy.deepcopy(meas) # next ens use
        simbadcells_18 = copy.deepcopy(meas)  # TRDI (pw6)
        simbadcells_19 = copy.deepcopy(meas)  # above
        simbadcells_20 = copy.deepcopy(meas)  # below
        simbadcells_22 = copy.deepcopy(meas)  # before (hold)
        simbadcells_23 = copy.deepcopy(meas)  # after (next)

        for transect, draftmin_9, draftmax_10, edgemin_11, edgemax_12, \
            ens_last_13, ens_next_14, cells_18, cells_19, cells_20, cells_22, cells_23 \
                in zip(meas.transects,
                       simdraftmin_9.transects,
                       simdraftmax_10.transects,
                       simedgemin_11.transects,
                       simedgemax_12.transects,
                       simbadens_last_13.transects,
                       simbadens_next_14.transects,
                       simbadcells_18.transects,
                       simbadcells_19.transects,
                       simbadcells_20.transects,
                       simbadcells_22.transects,
                       simbadcells_23.transects):
            if transect.checked:
                q = QComp()
                if skip_PP_min_max:
                    print('PP skipped') # TODO remove it
                else:
                    q.populate_data(data_in=transect, top_method='Power', bot_method='Power', exponent=exp_pp_min)
                    q_total_3min.append(q.total)
                    q_top_3min.append(q.top)
                    q_bot_3min.append(q.bottom)

                    q.populate_data(data_in=transect, top_method='Power', bot_method='Power', exponent=exp_pp_max)
                    q_total_3max.append(q.total)
                    q_top_3max.append(q.top)
                    q_bot_3max.append(q.bottom)

                if skip_NS_min_max:
                    print('NS skipped') # TODO remove it
                else:
                    q.populate_data(data_in=transect, top_method='Constant', bot_method='No Slip', exponent=exp_ns_min)
                    q_total_5min.append(q.total)
                    q_top_5min.append(q.top)
                    q_bot_5min.append(q.bottom)

                    q.populate_data(data_in=transect, top_method='Constant', bot_method='No Slip', exponent=exp_ns_max)
                    q_total_5max.append(q.total)
                    q_top_5max.append(q.top)
                    q_bot_5max.append(q.bottom)

                # Edge estimation
                init_dist_right = transect.edges.right.distance_m
                init_dist_left = transect.edges.left.distance_m

                # Select user percentage or default
                if d_right_error_prct_user is None:
                    d_right_error_prct = 0.20
                else:
                    d_right_error_prct = d_right_error_prct_user

                if d_left_error_prct_user is None:
                    d_left_error_prct = 0.20
                else:
                    d_left_error_prct = d_left_error_prct_user

                # Compute min distance for both edges
                min_left_dist = (1 - d_left_error_prct) * init_dist_left
                min_right_dist = (1 - d_right_error_prct) * init_dist_right

                if min_left_dist <= 0:
                    min_left_dist = 0.10
                if min_right_dist <= 0:
                    min_right_dist = 0.10

                self.d_right_error_min.append(min_right_dist)
                self.d_left_error_min.append(min_left_dist)

                # Simulation 9 (underestimation case)
                draftmin_9.edges.left.distance_m = min_left_dist
                draftmin_9.edges.right.distance_m = min_right_dist
                draftmin_9.edges.left.type = 'Triangular'
                draftmin_9.edges.right.type = 'Triangular'

                # Compute max distance for both edges
                max_left_dist = (1 + d_left_error_prct) * init_dist_left
                max_right_dist = (1 + d_right_error_prct) * init_dist_right

                self.d_right_error_max.append(max_right_dist)
                self.d_left_error_max.append(max_left_dist)

                # Simulation 10 (overestimation case)
                draftmax_10.edges.left.distance_m = max_left_dist
                draftmax_10.edges.right.distance_m = max_right_dist
                draftmax_10.edges.left.type = 'Rectangular'
                draftmax_10.edges.right.type = 'Rectangular'

                # Simulation 11 -0.02m - Simulation 12 +0.02m
                depths = transect.depths.bt_depths.depth_processed_m  # depth by ens
                depth_90 = np.quantile(depths, q=0.9) # quantile 90% to avoid spikes

                if draft_error_user is None:
                    if depth_90 < 2.50:
                        draft_error = 0.02
                    else:
                        draft_error = 0.05
                    draft_min = transect.depths.bt_depths.draft_orig_m - draft_error
                    draft_max = transect.depths.bt_depths.draft_orig_m + draft_error

                    if draft_min <=0:
                        draft_min = 0.01
                else:
                    draft_error = draft_error_user
                    draft_min = transect.depths.bt_depths.draft_orig_m - draft_error
                    draft_max = transect.depths.bt_depths.draft_orig_m + draft_error

                    if draft_min <=0:
                        draft_min = 0.01

                list_draft_error.append(draft_error)
                edgemin_11.change_draft(draft_min)
                edgemax_12.change_draft(draft_max)

                # Simulations 13 14 15 : ensemble interpolation
                # TODO the use of abba includes estimating invalid ensembles if data is not lost or missing, so these
                # are now duplicates of 22 and 23 if the entire ensemble is invalid.
                ens_last_13.w_vel.interpolate_ens_next()
                ens_next_14.w_vel.interpolate_ens_hold_last()

                # Simulations 18 to 25:  cells interpolation
                cells_18.w_vel.interpolate_cells_trdi(cells_18)
                # TODO Above, below, before, and after methods were not correct
                # cells_19.w_vel.interpolate_cells_above(cells_19)
                # cells_20.w_vel.interpolate_cells_below(cells_20)
                # cells_22.w_vel.interpolate_cells_before(cells_22)
                # cells_23.w_vel.interpolate_cells_after(cells_23)
                cells_19.w_vel.interpolate_abba(self, transect, search_loc=['above'])
                cells_20.w_vel.interpolate_abba(self, transect, search_loc=['below'])
                cells_22.w_vel.interpolate_abba(self, transect, search_loc=['before'])
                cells_23.w_vel.interpolate_abba(self, transect, search_loc=['after'])

        self.list_draft_error = list_draft_error

        if skip_PP_min_max:
            self.simu3min = self.simu3
            self.simu3max = self.simu3
        else:
            # Simulation 3min
            self.simu3min['q_total'] = q_total_3min
            self.simu3min['q_top'] = q_top_3min
            self.simu3min['q_bot'] = q_bot_3min
            # Simulation 3max
            self.simu3max['q_total'] = q_total_3max
            self.simu3max['q_top'] = q_top_3max
            self.simu3max['q_bot'] = q_bot_3max

        if skip_NS_min_max:
            self.simu5min = self.simu5
            self.simu5max = self.simu3
        else:
            # Simulation 5min
            self.simu5min['q_total'] = q_total_5min
            self.simu5min['q_top'] = q_top_5min
            self.simu5min['q_bot'] = q_bot_5min
            # Simulation 5max
            self.simu5max['q_total'] = q_total_5max
            self.simu5max['q_top'] = q_top_5max
            self.simu5max['q_bot'] = q_bot_5max

        # Compute discharge
        # Simulations related to edge estimation (R and L)
        simdraftmin_9.compute_discharge()
        simdraftmax_10.compute_discharge()

        # Simulations related to draft transducer
        simedgemin_11.compute_discharge()
        simedgemax_12.compute_discharge()

        # Missing ens cells
        simbadens_last_13.compute_discharge()
        simbadens_next_14.compute_discharge()
        simbadcells_18.compute_discharge()
        simbadcells_19.compute_discharge()
        simbadcells_20.compute_discharge()
        simbadcells_22.compute_discharge()
        simbadcells_23.compute_discharge()

        # Initialization
        q_total_9 = []
        q_right_9 = []
        q_left_9 = []
        q_total_10 = []
        q_right_10 = []
        q_left_10 = []
        q_total_11 = []
        q_top_11 = []
        q_right_11 = []
        q_left_11 = []
        q_total_12 = []
        q_top_12 = []
        q_right_12 = []
        q_left_12 = []
        q_total_13 = []
        q_middle_13 = []
        q_total_14 = []
        q_middle_14 = []
        q_total_18 = []
        q_middle_18 = []
        q_total_19 = []
        q_middle_19 = []
        q_total_20 = []
        q_middle_20 = []
        q_total_22 = []
        q_middle_22 = []
        q_total_23 = []
        q_middle_23 = []

        # Append discharges list in a loop
        for x in range(len(meas.transects)):
            if meas.transects[x].checked == 1:
                q_total_1.append(meas.discharge[x].total)
                q_top_1.append(meas.discharge[x].top)
                q_bot_1.append(meas.discharge[x].bottom)
                q_right_1.append(meas.discharge[x].right)
                q_left_1.append(meas.discharge[x].left)
                q_middle_1.append(meas.discharge[x].middle)

                q_total_9.append(simdraftmin_9.discharge[x].total)
                q_right_9.append(simdraftmin_9.discharge[x].right)
                q_left_9.append(simdraftmin_9.discharge[x].left)

                q_total_10.append(simdraftmax_10.discharge[x].total)
                q_right_10.append(simdraftmax_10.discharge[x].right)
                q_left_10.append(simdraftmax_10.discharge[x].left)

                q_total_11.append(simedgemin_11.discharge[x].total)
                q_top_11.append(simedgemin_11.discharge[x].top)
                q_right_11.append(simedgemin_11.discharge[x].right)
                q_left_11.append(simedgemin_11.discharge[x].left)

                q_total_12.append(simedgemax_12.discharge[x].total)
                q_top_12.append(simedgemax_12.discharge[x].top)
                q_right_12.append(simedgemax_12.discharge[x].right)
                q_left_12.append(simedgemax_12.discharge[x].left)

                q_total_13.append(simbadens_last_13.discharge[x].total)
                q_middle_13.append(simbadens_last_13.discharge[x].middle)

                q_total_14.append(simbadens_next_14.discharge[x].total)
                q_middle_14.append(simbadens_next_14.discharge[x].middle)

                q_total_18.append(simbadcells_18.discharge[x].total)
                q_middle_18.append(simbadcells_18.discharge[x].middle)

                q_total_19.append(simbadcells_19.discharge[x].total)
                q_middle_19.append(simbadcells_19.discharge[x].middle)

                q_total_20.append(simbadcells_20.discharge[x].total)
                q_middle_20.append(simbadcells_20.discharge[x].middle)

                q_total_22.append(simbadcells_22.discharge[x].total)
                q_middle_22.append(simbadcells_22.discharge[x].middle)

                q_total_23.append(simbadcells_23.discharge[x].total)
                q_middle_23.append(simbadcells_23.discharge[x].middle)

        # Store in self
        self.simu1['q_total'] = q_total_1
        self.simu1['q_top'] = q_top_1
        self.simu1['q_bot'] = q_bot_1
        self.simu1['q_right'] = q_right_1
        self.simu1['q_left'] = q_left_1
        self.simu1['q_middle'] = q_middle_1

        self.simu9['q_total'] = q_total_9
        self.simu9['q_right'] = q_right_9
        self.simu9['q_left'] = q_left_9

        self.simu10['q_total'] = q_total_10
        self.simu10['q_right'] = q_right_10
        self.simu10['q_left'] = q_left_10

        self.simu11['q_total'] = q_total_11
        self.simu11['q_top'] = q_top_11
        self.simu11['q_right'] = q_right_11
        self.simu11['q_left'] = q_left_11

        self.simu12['q_total'] = q_total_12
        self.simu12['q_top'] = q_top_12
        self.simu12['q_right'] = q_right_12
        self.simu12['q_left'] = q_left_12

        self.simu13['q_total'] = q_total_13
        self.simu13['q_middle'] = q_middle_13

        self.simu14['q_total'] = q_total_14
        self.simu14['q_middle'] = q_middle_14

        self.simu18['q_total'] = q_total_18
        self.simu18['q_middle'] = q_middle_18

        self.simu19['q_total'] = q_total_19
        self.simu19['q_middle'] = q_middle_19

        self.simu20['q_total'] = q_total_20
        self.simu20['q_middle'] = q_middle_20

        self.simu22['q_total'] = q_total_22
        self.simu22['q_middle'] = q_middle_22

        self.simu23['q_total'] = q_total_23
        self.simu23['q_middle'] = q_middle_23

        # Delete Measurement objects
        # TODO : I'm not sure that deleting is needed since the function do not store any data
        del simdraftmin_9
        del simdraftmax_10
        del simedgemin_11
        del simedgemax_12
        del simbadens_last_13
        del simbadens_next_14
        del simbadcells_18
        del simbadcells_19
        del simbadcells_20
        del simbadcells_22
        del simbadcells_23

    def compute_combined_uncertainty(self):
        """
        Combined the uncertainty for each transect and for the measurement

        :return: computed values combined, total and contributions
        """

        # Create a Dataframe with all computed uncertainty for each checked transect
        TABLE_u = pd.DataFrame()
        TABLE_u['u_syst'] = self.u_syst_list
        TABLE_u['u_movbed'] = self.u_movbed_list
        TABLE_u['u_meas'] = self.u_meas_list  # the only purely random uncertainty component source
        TABLE_u['u_ens'] = self.u_ens_list
        TABLE_u['u_badcell'] = self.u_badcell_list
        TABLE_u['u_badens'] = self.u_badens_list
        TABLE_u['u_top'] = self.u_top_list
        TABLE_u['u_bot'] = self.u_bot_list
        TABLE_u['u_left'] = self.u_left_list
        TABLE_u['u_right'] = self.u_right_list
        if self.u_cov_68_user is not None:
            TABLE_u['u_cov'] = 0.01 * self.u_cov_68_user
        else:
            TABLE_u['u_cov'] = 0.01*self.cov_68

        # Convert uncertainty (68% level of confidence) into variance
        # Note that only variance is additive
        TABLE_u2 = TABLE_u.applymap(lambda x: x ** 2)

        # Combined uncertainty by transect
        # sum of variance of each component, then sqrt, then multiply by 100 for percentage
        self.u_combined_by_transect = [100 * (x ** 0.5) for x in list(TABLE_u2.sum(axis=1))]
        self.U_total_by_transect = [2 * x for x in self.u_combined_by_transect]

        # Uncertainty for the measurement
        # The only random source is from the measured area
        u2_alea = TABLE_u2['u_meas'].mean()

        # All other sources are systematic (mostly due to computation method and values from user)
        u2_syst = list(TABLE_u2.drop(['u_meas'], axis=1).mean())

        # Combined all uncertainty sources
        # If the user change the u_meas term, then it is not averaged out
        if self.u_meas_mean_user is not None:
            u2_c_gauging = ((0.01 * self.u_meas_mean_user)**2) + sum(u2_syst)
        else:
            u2_c_gauging = (1 / self.nb_transects) * u2_alea + sum(u2_syst)
        u_combined_total = 100 * (u2_c_gauging ** 0.5)
        U_total_95 = 2 * u_combined_total

        # # Add coeff of variation only if larger than the combined uncertainty
        # if (self.cov_68 - u_combined_total) > 0:
        #     print("Adding coefficient of variation")
        #     TABLE_u['u_cov'] = 0.01 * self.cov_68
        #     TABLE_u2 = TABLE_u.applymap(lambda x: x ** 2)
        #     self.u_combined_by_transect = [100 * (x ** 0.5) for x in list(TABLE_u2.sum(axis=1))]
        #     self.U_total_by_transect = [2 * x for x in self.u_combined_by_transect]
        #     u2_alea = TABLE_u2['u_meas'].mean()
        #     u2_syst = list(TABLE_u2.drop(['u_meas'], axis=1).mean())
        #     u2_c_gauging = (1 / self.nb_transects) * u2_alea + sum(u2_syst)
        #     u_combined_total = 100 * (u2_c_gauging ** 0.5)
        #     U_total_95 = 2 * u_combined_total
        #
        # if self.u_cov_68_user is not None:
        #     TABLE_u['u_cov'] = 0.01 * self.u_cov_68_user
        #     TABLE_u2 = TABLE_u.applymap(lambda x: x ** 2)
        #     self.u_combined_by_transect = [100 * (x ** 0.5) for x in list(TABLE_u2.sum(axis=1))]
        #     self.U_total_by_transect = [2 * x for x in self.u_combined_by_transect]
        #     u2_alea = TABLE_u2['u_meas'].mean()
        #     u2_syst = list(TABLE_u2.drop(['u_meas'], axis=1).mean())
        #     u2_c_gauging = (1 / self.nb_transects) * u2_alea + sum(u2_syst)
        #     u_combined_total = 100 * (u2_c_gauging ** 0.5)
        #     U_total_95 = 2 * u_combined_total

        # Average of each terms
        # Average contribution to the combined uncertainty
        # Measured uncertainty then other uncertainty sources
        u_terms = []
        contrib_terms_total = []
        if self.u_meas_mean_user is not None:
            u_terms.append(self.u_meas_mean_user)
            contrib_terms_total.append(100 * ( ((0.01 * self.u_meas_mean_user) ** 2) ) / u2_c_gauging)
        else:
            u_terms.append(100 * ((1 / self.nb_transects) * TABLE_u2['u_meas'].mean()) ** 0.5)
            contrib_terms_total.append(100 * ((1 / self.nb_transects) * TABLE_u2['u_meas'].mean()) / u2_c_gauging)
        u_terms = u_terms + [100 * x ** 0.5 for x in u2_syst]
        contrib_terms_total = contrib_terms_total + [100 * x / u2_c_gauging for x in u2_syst]

        # Store results : reordering so that syst, moving bed and measured are the three first sources
        self.u_terms = [u_terms[i] for i in [2, 1, 0, 3, 4, 5, 6, 7, 8, 9, 10]]
        self.u_combined_total = u_combined_total
        self.U_total_95 = U_total_95
        self.variance_terms_by_transect = TABLE_u2
        self.contrib_terms_total = [contrib_terms_total[i] for i in [2, 1, 0, 3, 4, 5, 6, 7, 8, 9, 10]]
        self.contrib_legend = list(TABLE_u.columns)

        # Convert relative uncertainties in m3/s and relative variance in m6/s2
        self.u_syst_mean_abs = self.u_syst_mean*np.mean(self.simu1['q_total'])
        self.u_combined_by_transect_abs = np.asarray(self.u_combined_by_transect)*np.asarray(self.simu1['q_total'])*0.01
        self.u_terms_abs = np.asarray(self.u_terms)*0.01*np.mean(self.simu1['q_total'])
        self.u_combined_total_abs = 0.01*self.u_combined_total*np.mean(self.simu1['q_total'])
        self.U_total_by_transect_abs = np.asarray(self.U_total_by_transect)*np.asarray(self.simu1['q_total'])*0.01
        self.U_total_95_abs = 0.01*self.U_total_95*np.mean(self.simu1['q_total'])
        self.variance_terms_by_transect_abs=np.transpose(np.transpose(self.variance_terms_by_transect)*np.asarray(self.simu1['q_total'])**2)

    def measured_area_uncertainty(self,
                                  meas,
                                  u_prct_dzi_user,
                                  r_corr_cell_user,
                                  amb_vel_user,
                                  nb_cyc_user,
                                  r_corr_signal_user,
                                  n_pings_wt_user):

        # Assume 0.5% uncertainty on cell size
        if u_prct_dzi_user is not None:
            self.u_prct_dzi = 0.01 * u_prct_dzi_user
        else:
            self.u_prct_dzi = 0.5 * 0.01  # k=1 0.5%

        # Correlation of uncertainties related to the water velocity of contiguous cells
        # 100% or user override (between 0 and 1)
        if r_corr_cell_user is not None:
            self.r_corr_cell = r_corr_cell_user
        else:
            self.r_corr_cell = 1

        # The ambiguity velocity 0.50 m/s or user override
        # TODO Ambiguity velocity could be obtained from TRDI data
        if amb_vel_user is not None:
            self.amb_vel = amb_vel_user
        else:
            self.amb_vel = 0.50

        # Number of carrier cycles per pulse coded element, default is 4 or override
        if nb_cyc_user is not None:
            self.nb_cyc = nb_cyc_user
        else:
            self.nb_cyc = 4

        # Correlation of the beam signal
        if r_corr_signal_user is not None:
            self.r_corr_signal = r_corr_signal_user
        else:
            self.r_corr_signal = 0.8

        # Number of water ping
        if n_pings_wt_user is not None:
            self.n_pings_wt = n_pings_wt_user
        else:
            self.n_pings_wt = 1

        # Compute the uncertainty due to the measured area
        self.u_meas_compute(meas=meas,
                            u_prct_dzi=self.u_prct_dzi,
                            r_corr=self.r_corr_cell,
                            V_a=self.amb_vel,
                            Cyc=self.nb_cyc,
                            R_corr=self.r_corr_signal,
                            n_pings_wt=self.n_pings_wt)

    @staticmethod
    def compute_moving_bed_uncertainty(meas):
        return 0.01 * meas.uncertainty.moving_bed_95 / 2

    @staticmethod
    def compute_systematic_uncertainty():
        return 0.01 * 1.31

    @staticmethod
    def depth_error_boat_motion(transect):
        """Relative depth error due to vertical velocity of boat
           the height [m] is vertical velocity times ensemble duration
       """

        d_ens = transect.depths.bt_depths.depth_processed_m
        depth_vv = transect.boat_vel.bt_vel.w_mps * transect.date_time.ens_duration_sec
        relative_error_depth = np.abs(depth_vv) / d_ens
        relative_error_depth[np.isnan(relative_error_depth)] = 0.00
        return relative_error_depth

    @staticmethod
    def boat_std_by_equation(transect):
        """Computes a theoretical relative standard deviation of boat velocity using an equation from Shaw and Brumley (1993)
        """

        # Compute boat speed
        u_boat = transect.boat_vel.bt_vel.u_processed_mps
        v_boat = transect.boat_vel.bt_vel.v_processed_mps
        v_bm_ens_abs = np.sqrt(u_boat ** 2 + v_boat ** 2)

        freq_v_boat_adcp = np.asarray(list(transect.boat_vel.bt_vel.frequency_khz))
        d_ens = transect.depths.bt_depths.depth_processed_m

        # Apply equation
        u_prct_v_boatm_ens = 0.01 * ((0.03 * v_bm_ens_abs) +
                                     ((1 + (0.3 * v_bm_ens_abs)) /
                                      (1 + (0.0001 * d_ens * freq_v_boat_adcp)))) / v_bm_ens_abs

        # TODO : try another limit 100% instead of 50% / or add it as a parametr to test it
        # the inverse of velocity may lead to high values of uncertainty : the limit is set at 50%
        u_prct_v_boatm_ens[u_prct_v_boatm_ens > 0.5] = 0.5
        u_prct_v_boatm_ens[np.isnan(u_prct_v_boatm_ens)] = 0.00
        return u_prct_v_boatm_ens

    @staticmethod
    def water_std_by_equation(transect, V_a, Cyc, R_corr, n_pings_wt):
        """Compute a theoretical relative standard deviation of water velocity uisng equation for broadband from RDI (1996)
        """

        # Computer water speed
        u_water = transect.w_vel.u_processed_mps
        v_water = transect.w_vel.v_processed_mps
        v_wa_cell_abs = np.sqrt(u_water ** 2 + v_water ** 2)

        # Get data for equation
        c_speed = transect.sensors.speed_of_sound_mps.internal.data
        teta = transect.adcp.beam_angle_deg
        freq_v_water_adcp = np.asarray(list(transect.w_vel.frequency))
        freq = freq_v_water_adcp * 1000
        depth_cell = np.mean(transect.depths.bt_depths.depth_cell_size_m, axis=0)

        # Compute equation
        u_wt_bb = ((1.5 * V_a) / math.pi) * (((Cyc * (R_corr ** (-2) - 1) * c_speed * math.cos(
            math.radians(teta))) / (freq * depth_cell * n_pings_wt)) ** 0.5)

        u_prct_v_water = np.abs(u_wt_bb) / np.abs(v_wa_cell_abs)
        u_prct_v_water_ens = np.nanmean(u_prct_v_water, axis=0)
        u_prct_v_water_ens[np.isnan(u_prct_v_water_ens)] = 0.00
        # Limit the maximum relative uncertainty to 100%
        # TODO this is not always true the standard deviation can be greater than the mean water velocity.
        u_prct_v_water_ens[u_prct_v_water_ens > 1] = 1
        return u_prct_v_water_ens

    @staticmethod
    def water_std_by_error_velocity(transect):
        """Compute the relative standard deviation of the water velocity using the fact that the error velocity is scaled so that the standard deviation of the error velocity is the same as the standard deviation of the horizontal water velocity.
        """

        # Computer water speed
        u_water = transect.w_vel.u_processed_mps
        v_water = transect.w_vel.v_processed_mps
        v_wa_cell_abs = np.sqrt(u_water ** 2 + v_water ** 2)

        # Use only valid error velocity data
        d_vel_filtered = np.tile([np.nan], transect.w_vel.d_vel.shape)
        d_vel_filtered = transect.w_vel.d_vel[transect.w_vel.valid_data[0]]

        # Compute relative standard deviation of error velocity
        std_ev_WT = np.nanstd(d_vel_filtered) / np.abs(v_wa_cell_abs)
        std_ev_WT_ens = np.nanmedian(std_ev_WT, axis=0)
        # TODO consider substituting the overall std for nan rather than 0
        # all_std_ev_WT = np.nanstd(d_vel_filtered[:])
        # std_ev_WT_ens[np.isnan(std_ev_WT_ens)] = all_std_ev_WT
        std_ev_WT_ens[np.isnan(std_ev_WT_ens)] = 0.00
        return std_ev_WT_ens

    @staticmethod
    def boat_std_by_error_velocity(transect):
        """Compute the relative standard deviation of the boat velocity using the fact that the error velocity is scaled so that the standard deviation of the error velocity is the same as the standard deviation of the horizontal boat velocity.
        """

        # Compute boat speed
        u_boat = transect.boat_vel.bt_vel.u_processed_mps
        v_boat = transect.boat_vel.bt_vel.v_processed_mps
        v_bm_ens_abs = np.sqrt(u_boat ** 2 + v_boat ** 2)

        # Use only valid error velocity data
        d_vel_filtered = np.tile([np.nan], transect.boat_vel.bt_vel.d_vel.shape)
        d_vel_filtered = transect.boat_vel.bt_vel.d_vel[transect.boat_vel.bt_vel.valid_data[0]]

        # Compute relative standard deviation of error velocity
        all_std_ev_BT = np.nanstd(transect.boat_vel.bt_vel.d_vel_filtered)
        std_ev_BT = np.abs(all_std_ev_BT) / v_bm_ens_abs
        # TODO Consider substituting the overal std for nan rather than 0
        # std_ev_BT[np.isnan(std_ev_BT)] = all_std_ev_BT
        std_ev_BT[np.isnan(std_ev_BT)] = 0.00
        return std_ev_BT

    @staticmethod
    def compute_meas_cov(meas):
        """Compute the coefficient of variation of the total transect discharges used in the measurment.
        """
        if self.nb_transects > 1:
            cov_68 = np.nan
            total_q = []
            for n in range(self.nb_transects):
                if meas.transects[n].checked:
                    total_q.append(meas.discharge[n].total)
            if len(total_q) > 1:
                # Compute coefficient of variation
                cov = np.abs(np.nanstd(total_q, ddof=1) / np.nanmean(total_q)) * 100

                # Inflate the cov to the 95% value
                if len(total_q) == 2:
                    # Use the approximate method as taught in class to reduce the high coverage factor for 2 transects
                    # and account for prior knowledge related to 720 second duration analysis
                    cov_95 = cov * 3.3
                    cov_68 = cov_95 / 2
                else:
                    # Use Student's t to inflate COV for n > 2
                    cov_95 = t.interval(0.95, n_max - 1)[1] * cov / n_max ** 0.5
                    cov_68 = cov_95 / 2
            else:
                cov_68 = np.nan

        return cov_68

    def plot_u_meas_contrib(self, plot=False, name_plot_u_meas='Contrib_u_meas.png'):
        """
        Plot a barplot showing the contribution of uncertainty terms to the measured uncertainty

        :param plot:
            if True save the barplot
        :param name_plot_u_meas:
            name of the file to be saved if plot is True
        :return:
        """
        # ----- Store in dataframe
        Contrib_meas = pd.DataFrame()
        Contrib_meas['v_boat'] = self.u_contrib_meas_v_boat
        Contrib_meas['error_vel_boat'] = self.u_contrib_errv_v_boat
        Contrib_meas['depth vertical_vel_boat'] = self.u_contrib_verv_h_depth
        Contrib_meas['error_vel_water'] = self.u_contrib_errv_v_wate
        Contrib_meas['v_water'] = self.u_contrib_meas_v_wate
        Contrib_meas['cell size'] = self.u_contrib_meas_u_dzi
        Contrib_meas_prct = 100 * Contrib_meas  # Convert into percentage

        # ----- Plot
        plt.rcParams.update({'font.size': 14})
        Contrib_meas_prct.plot.bar(stacked=True, figsize=(10, 7))
        plt.xlabel('Transect index')
        plt.grid(True, linestyle='--', axis='y')
        plt.ylabel('Contribution to $u_{meas}$ uncertainty [%]')

        if self.u_meas_mean_user is not None:
            plt.legend(title=" WARNING ! \n $u_{meas}$ has been \n modified by the user", labels=[],
                       shadow=False, framealpha=1,
                       title_fontsize=40,
                       loc="center",
                       bbox_to_anchor=(0.5, 0.5))
        else:
            plt.legend(title="Error sources",
                   loc="center left",
                   labelspacing=-2.1,
                   frameon=False,
                   bbox_to_anchor=(1, 0.5))

        # ---- If plot is True save the plot
        if plot:
            plt.savefig(name_plot_u_meas, bbox_inches='tight')
        plt.show()

    def plot_u_contrib(self, plot=False, name_plot_u_contrib='Contrib_u.png'):
        """
        Plot a barplot showing the contribution in terms of variance
        of each uncertainty component for each transect

        :param plot:
            if True save the plot in a file
        :param name_plot_u_contrib:
            name of the file to be saved if plot is True
        :return: barplot
        """
        # --- Variance in m6/s2
        Contrib_all = self.variance_terms_by_transect_abs  # m6/s2
        list_basic_color_oursin = [u'#d62728', u'#7f7f7f', u'#ff7f0e', 'gold',
                                   u'#bcbd22', u'#2ca02c', u'#e377c2',
                                   u'#8c564b', u'#17becf', u'#1f77b4', u'#9467bd']
        # ----- Plot
        plt.rcParams.update({'font.size': 14})
        Contrib_all.plot.bar(stacked=True, color=list_basic_color_oursin, figsize=(10, 7))
        plt.xlabel('Transect index')
        plt.grid(True, linestyle='--', axis='y')
        # plt.ylabel('Sum of variance [%]')
        plt.ylabel(r'Variance [$m^6/s^{-2}$]')
        plt.legend(title="Uncertainty components",
                   loc="center left",
                   labelspacing=-2.1,
                   frameon=False,
                   bbox_to_anchor=(1, 0.5))

        plt.title("U(Q) = " + str('%.1f' % self.U_total_95) +
                  "% PP: " + str('%.2f' % self.exp_pp_min) +
                  "-" + str('%.2f' % self.exp_pp_max) + " NS: " +
                  str('%.2f' % self.exp_ns_min) + "-" +
                  str('%.2f' % self.exp_ns_max))



        # ---- If plot is True save the plot
        if plot:
            plt.savefig(name_plot_u_contrib, bbox_inches='tight')
        plt.show()

    def plot_u_contrib_relative(self, plot=False, name_plot_u_contrib='Contrib_u.png'):
        """
        Plot a barplot showing the contribution in terms of variance
        of each uncertainty component for each transect

        :param plot:
            if True save the plot in a file
        :param name_plot_u_contrib:
            name of the file to be saved if plot is True
        :return: barplot
        """
        # --- Variance in m6/s2
        Contrib_all = 100*100*self.variance_terms_by_transect  # m6/s2
        list_basic_color_oursin = [u'#d62728', u'#7f7f7f', u'#ff7f0e', 'gold',
                                   u'#bcbd22', u'#2ca02c', u'#e377c2',
                                   u'#8c564b', u'#17becf', u'#1f77b4', u'#9467bd']
        # ----- Plot
        plt.rcParams.update({'font.size': 14})
        Contrib_all.plot.bar(stacked=True, color=list_basic_color_oursin, figsize=(10, 7))
        plt.xlabel('Transect index')
        plt.grid(True, linestyle='--', axis='y')
        plt.ylabel('Sum of variance [%]')
        # plt.ylabel(r'Variance [$m^6/s^{-2}$]')
        plt.legend(title="Uncertainty components",
                   loc="center left",
                   labelspacing=-2.1,
                   frameon=False,
                   bbox_to_anchor=(1, 0.5))

        plt.title("U(Q) = " + str('%.1f' % self.U_total_95) +
                  "% PP: " + str('%.2f' % self.exp_pp_min) +
                  "-" + str('%.2f' % self.exp_pp_max) + " NS: " +
                  str('%.2f' % self.exp_ns_min) + "-" +
                  str('%.2f' % self.exp_ns_max))

        # ---- If plot is True save the plot
        if plot:
            plt.savefig(name_plot_u_contrib, bbox_inches='tight')
        plt.show()

    def plot_u_mean_pie(self, plot=False, name_plot_u_pie='Mean_pie_u.png'):
        """
        Plot a pie showing the average contribution of each uncertainty source to the total uncertainty

        :param plot:
            if True save the figure
        :param name_plot_u_pie:
            Name of the file if plot is True
        :return: plot
        """
        list_basic_color_oursin = [u'#d62728', u'#7f7f7f', u'#ff7f0e', 'gold',
                                   u'#bcbd22', u'#2ca02c', u'#e377c2',
                                   u'#8c564b', u'#17becf', u'#1f77b4', u'#9467bd']

        def my_autopct(pct):
            return (str('%.1f' % pct) + '%') if pct > 2 else ''

        u_terms = [self.u_terms[i] for i in [1, 0, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
        contrib_terms_total = [self.contrib_terms_total[i] for i in [1, 0, 2, 3, 4, 5, 6, 7, 8, 9, 10]]

        plt.rcParams.update({'font.size': 14})
        plt.pie(x=contrib_terms_total,
                colors=list_basic_color_oursin,
                autopct=my_autopct,  # lambda x: str(round(x, 2)) + '%',
                pctdistance=1.25
                )
        plt.legend(labels=[str(y) + ' = ' + str('%.1f' % x) + '%' for x, y in zip(u_terms, self.contrib_legend)],
                   title="Uncertainty components (68% IC)",
                   loc="center left",
                   labelspacing=-2.1,
                   frameon=False,
                   bbox_to_anchor=(1, 0.5))
        if plot:
            plt.savefig(name_plot_u_pie, bbox_inches='tight')
        plt.show()

    @staticmethod
    def apply_u_rect(list_simu):
        # Compute the uncertainty using list of simulated discharges following a ranctangular law
        simu = pd.DataFrame()
        for i in range(len(list_simu)):
            name_col = 'simu' + str(i)
            simu[name_col] = list_simu[i]
        u_rect = (simu.max(axis=1) - simu.min(axis=1)) / (2 * (3 ** 0.5))

        return (u_rect)
