import pandas as pd
import copy
from Classes.BoatStructure import *
from Classes.QComp import QComp
import math
from scipy.stats import t
from profilehooks import profile
# import matplotlib.pyplot as plt


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
    u_total_95_user: float
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
    u_total_by_transect: list
        List that contains the total combined uncertainty (95%) for each transect
    u_total_95: float
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
    u_total_by_transect_abs: list
        List that contains the total combined uncertainty (95%) for each transect
    u_total_95_abs: float
        Total uncertainty (95%) for the measurement
    variance_terms_by_transect_abs: DataFrame
        Variance (68% m6/s2) for each term and for each transect


    nb_transects: float
        Number of transects used

    # --- Store results of all simulations in DataFrame
    sim_original: DataFrame
        Discharges (total, and subareas) computed for simulation 1
    sim_extrap_pp_16: DataFrame
        Discharges (total, and subareas) computed for simulation 2
    sim_extrap_pp_min: DataFrame
        Discharges (total, and subareas) computed for simulation 3
    simu3min: DataFrame
        Discharges (total, and subareas) computed for simulation 3min
    simu3max: DataFrame
        Discharges (total, and subareas) computed for simulation 3max
    sim_extrap_cns_16: DataFrame
        Discharges (total, and subareas) computed for simulation 4
    sim_extrap_cns_min: DataFrame
        Discharges (total, and subareas) computed for simulation 5
    simu5min: DataFrame
        Discharges (total, and subareas) computed for simulation 5min
    simu5max: DataFrame
        Discharges (total, and subareas) computed for simulation 5max
    sim_extrap_3pns_16: DataFrame
        Discharges (total, and subareas) computed for simulation 6
    sim_extrap_3pns_opt: DataFrame
        Discharges (total, and subareas) computed for simulation 7
    simu8: DataFrame # not used
        Discharges (total, and subareas) computed for simulation 8
    sim_edge_min: DataFrame # edge
        Discharges (total, and subareas) computed for simulation 9
    sim_edge_max: DataFrame # edge
        Discharges (total, and subareas) computed for simulation 10
    sim_draft_min: DataFrame # draft
        Discharges (total, and subareas) computed for simulation 11
    sim_draft_max: DataFrame # draft
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
    sim_cells_trdi: DataFrame # missing cells
        Discharges (total, and subareas) computed for simulation 18
    sim_cells_above: DataFrame # missing cells
        Discharges (total, and subareas) computed for simulation 19
    sim_cells_below: DataFrame # missing cells
        Discharges (total, and subareas) computed for simulation 20
    sim_cells_before: DataFrame # missing cells
        Discharges (total, and subareas) computed for simulation 22
    sim_cells_after: DataFrame # missing cells
        Discharges (total, and subareas) computed for simulation 23

    simu_checked: Dict
        Dict that shows which simulation are used to compute the uncertainty
    simu_checked_user: Dict
        User provided dict for selecting which simulation to be used to compute the uncertainty
    simu_discharge: Dict
        Dict that gathers all simulations
    checked_idx: list
        List of indices of checked transects
    """

    def __init__(self):
        """Initialize class and instance variables."""

        # User provided parameters
        # TODO consider making this a dictionary of user_overrides
        self.exp_pp_min_user = None  # float
        self.exp_pp_max_user = None
        self.exp_ns_min_user = None
        self.exp_ns_max_user = None
        self.draft_error_user = None  # [m]
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
        self.u_total_95_user = None
        
        # Internally set parameters
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

        # Terms computed by transect (list at 68% level)
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

        # Term computed for measurement
        self.cov_68 = None

        # Relative contribution of each component to the measured uncertainty by transect
        self.u_contrib_meas_v_boat = []
        self.u_contrib_errv_v_boat = []
        self.u_contrib_verv_h_depth = []
        self.u_contrib_errv_v_wate = []
        self.u_contrib_meas_v_wate = []
        self.u_contrib_meas_u_dzi = []

        # Overall measurement average
        self.u_syst_mean = None
        self.u_combined_by_transect = []
        self.u_total_by_transect = []
        self.u_terms = []
        self.u_combined_total = None
        self.u_total_95 = None
        self.variance_terms_by_transect = pd.DataFrame()
        self.contrib_terms_total = []
        self.contrib_legend = []
        self.nb_transects = None

        # Absolute uncertainties
        self.u_syst_mean_abs = None
        self.u_combined_by_transect_abs = []
        self.u_terms_abs = []
        self.u_combined_total_abs = []
        self.u_total_by_transect_abs = []
        self.u_total_95_abs = None
        self.variance_terms_by_transect_abs = pd.DataFrame()

        # --- Store results of all simulations in DataFrame
        self.sim_original = pd.DataFrame(columns=['q_total', 'q_top', 'q_bot', 'q_left', 'q_right', 'q_middle'])
        self.sim_extrap_pp_16 = pd.DataFrame(columns=['q_total', 'q_top', 'q_bot'])
        self.sim_extrap_pp_opt = pd.DataFrame(columns=['q_total', 'q_top', 'q_bot'])
        self.sim_extrap_pp_min = pd.DataFrame(columns=['q_total', 'q_top', 'q_bot'])
        self.sim_extrap_pp_max = pd.DataFrame(columns=['q_total', 'q_top', 'q_bot'])
        self.sim_extrap_cns_16 = pd.DataFrame(columns=['q_total', 'q_top', 'q_bot'])
        self.sim_extrap_cns_opt = pd.DataFrame(columns=['q_total', 'q_top', 'q_bot'])
        self.sim_extrap_cns_min = pd.DataFrame(columns=['q_total', 'q_top', 'q_bot'])
        self.sim_extrap_cns_max = pd.DataFrame(columns=['q_total', 'q_top', 'q_bot'])
        self.sim_extrap_3pns_16 = pd.DataFrame(columns=['q_total', 'q_top', 'q_bot'])
        self.sim_extrap_3pns_opt = pd.DataFrame(columns=['q_total', 'q_top', 'q_bot'])
        self.sim_edge_min = pd.DataFrame(columns=['q_total', 'q_left', 'q_right'])
        self.sim_edge_max = pd.DataFrame(columns=['q_total', 'q_left', 'q_right'])
        self.sim_draft_min = pd.DataFrame(columns=['q_total', 'q_top', 'q_left', 'q_right'])
        self.sim_draft_max = pd.DataFrame(columns=['q_total', 'q_top', 'q_left', 'q_right'])
        self.sim_cells_trdi = pd.DataFrame(columns=['q_total', 'q_middle'])
        self.sim_cells_above = pd.DataFrame(columns=['q_total', 'q_middle'])
        self.sim_cells_below = pd.DataFrame(columns=['q_total', 'q_middle'])
        self.sim_cells_before = pd.DataFrame(columns=['q_total', 'q_middle'])
        self.sim_cells_after = pd.DataFrame(columns=['q_total', 'q_middle'])
        self.simu24 = pd.DataFrame()  # missing cells
        self.simu25 = pd.DataFrame()  # missing cells

        # simulation used or not
        self.simu_checked = dict()
        self.simu_checked_user = dict()
        self.simu_discharge = dict()

        self.checked_idx = []

    @profile
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
                       u_total_95_user=None,
                       simu_checked_user=None,
                       u_prct_dzi_user=None
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
        u_total_95_user: float
            User provided estimate of 95% total uncertainty (in %)
        simu_checked_user: Dict
            User provided dict for selecting which simulation to be used to compute the uncertainty
        u_prct_dzi_user: float
            User provided uncertainty related to depth cell size
        """

        self.transect_extrap_data_prep(meas)

        # 1. Systematic terms + correction terms (moving bed)
        #   1.a. Moving-bed / Same than QRev or user override
        self.compute_moving_bed_uncertainty(meas=meas, u_movbed_user=u_movbed_user)

        #   1.b.  Systematic. Use 1.31% or user override
        self.compute_systematic_uncertainty(u_syst_mean_user=u_syst_mean_user)

        # 2. Measured uncertainty
        #   2.a. Measured area BY EQUATION
        # Standard relative uncertainty of depth cell size 0.5% or user override
        self.measured_area_uncertainty(meas=meas, u_meas_mean_user=u_meas_mean_user)

        #   2.b. Coefficient of variation (same as QRev but 68% level of confidence) or user override
        self.compute_meas_cov(meas=meas, u_cov_68_user=u_cov_68_user)

        #   2.c. Uncertianty based on number of ensembles
        self.compute_number_ensembles_uncertainty(meas, u_ens_user)

        # 3. Run all the simulations to compute possible discharges
        self.run_oursin_simulations(meas, exp_pp_min_user, exp_pp_max_user, exp_ns_min_user, exp_ns_max_user,
                                    draft_error_user, d_right_error_prct_user, d_left_error_prct_user)

        # 4. Compute terms based on possible simulations and assuming a rectangular law

        # Uncertainty due to invalid cells and ensembles
        self.u_badcell_list = Oursin.apply_u_rect(list_sims=[self.sim_original,
                                                             self.sim_cells_trdi,
                                                             self.sim_cells_above,
                                                             self.sim_cells_below,
                                                             self.sim_cells_before,
                                                             self.sim_cells_after],
                                                  col_name='q_total') \
            / self.sim_original['q_total']

        if u_badcell_user is not None:
            self.u_badcell_user_list = [0.01 * u_badcell_user] * self.nb_transects
            self.u_badcell_user = u_badcell_user
        else:
            self.u_badcell_user_list = self.u_badcell_list

        # Uncertainty of top discharge extrapolation
        self.u_top_list = Oursin.apply_u_rect(list_sims=[self.sim_original,
                                                         self.sim_extrap_pp_opt,
                                                         self.sim_extrap_pp_min,
                                                         self.sim_extrap_pp_max,
                                                         self.sim_extrap_cns_opt,
                                                         self.sim_extrap_cns_min,
                                                         self.sim_extrap_cns_max,
                                                         self.sim_extrap_3pns_opt,
                                                         self.sim_draft_max,
                                                         self.sim_draft_min],
                                              col_name='q_top') \
            / self.sim_original['q_total']

        if u_top_mean_user is not None:
            self.u_top_mean_user_list = [0.01 * u_top_mean_user] * self.nb_transects
            self.u_top_mean_user = u_top_mean_user
        else:
            self.u_top_mean_user_list = self.u_top_list

        # Uncertainty of bottom discharge extrapolation
        self.u_bot_list = Oursin.apply_u_rect(list_sims=[self.sim_original,
                                                         self.sim_extrap_pp_opt,
                                                         self.sim_extrap_pp_min,
                                                         self.sim_extrap_pp_max,
                                                         self.sim_extrap_cns_opt,
                                                         self.sim_extrap_cns_min,
                                                         self.sim_extrap_cns_max,
                                                         self.sim_extrap_3pns_opt],
                                              col_name='q_bot') \
            / self.sim_original['q_total']

        if u_bot_mean_user is not None:
            self.u_bot_mean_user_list = [0.01 * u_bot_mean_user] * self.nb_transects
            self.u_bot_mean_user = u_bot_mean_user
        else:
            self.u_bot_mean_user_list = self.u_bot_list

        # Uncertainty of left edge discharge estimation
        self.u_left_list = Oursin.apply_u_rect(list_sims=[self.sim_original['q_left'],
                                                          self.sim_edge_min,
                                                          self.sim_edge_max,
                                                          self.sim_draft_min,
                                                          self.sim_draft_max],
                                               col_name='q_left') \
            / self.sim_original['q_total']

        if u_left_mean_user is not None:
            self.u_left_mean_user_list = [0.01 * u_left_mean_user] * self.nb_transects
            self.u_left_mean_user = u_left_mean_user
        else:
            self.u_left_mean_user_list = self.u_left_list

        # Uncertainty of right edge discharge estimation
        self.u_right_list = Oursin.apply_u_rect(list_sims=[self.sim_original['q_left'],
                                                          self.sim_edge_min,
                                                          self.sim_edge_max,
                                                          self.sim_draft_min,
                                                          self.sim_draft_max],
                                               col_name='q_right') \
            / self.sim_original['q_total']

        if u_right_mean_user is not None:
            self.u_right_mean_user_list = [0.01 * u_right_mean_user] * self.nb_transects
            self.u_right_mean_user = u_right_mean_user
        else:
            self.u_right_mean_user_list = self.u_right_list

        # 6. Combined by transects and contribution
        #    Evaluate the coefficient of variation and add it if cov²>oursin²
        self.u, self.u_meas, self.u_dsm, self.u_meas_dsm = \
            self.compute_combined_uncertainty(u_syst=self.u_syst_list,
                                              u_movbed=self.u_movbed_list,
                                              u_meas=self.u_meas_list,
                                              u_ens=self.u_ens_list,
                                              u_badcell=self.u_badcell_list,
                                              u_top=self.u_top_list,
                                              u_bot=self.u_bot_list,
                                              u_left=self.u_left_list,
                                              u_right=self.u_right_list,
                                              cov_68=self.cov_68)

        # self.u_user, self.u_meas_user, self.u_dsm_user, self.u_meas_dsm_user = \
        #     self.compute_combined_uncertainty(u_syst=self.u_syst_mean_user_list,
        #                                       u_movbed=self.u_movbed_user_list,
        #                                       u_meas=self.u_meas_mean_user_list,
        #                                       u_ens=self.u_ens_user_list,
        #                                       u_badcell=self.u_badcell_user_list,
        #                                       u_top=self.u_top_mean_user_list,
        #                                       u_bot=self.u_bot_mean_user_list,
        #                                       u_left=self.u_left_mean_user_list,
        #                                       u_right=self.u_right_mean_user_list,
        #                                       cov_68=self.cov_68)
        # # Use user provided uncertainty
        # if u_total_95_user is not None:
        #     self.u_total_95 = u_total_95_user
        #     self.u_total_95_user = u_total_95_user

    @staticmethod
    def compute_combined_uncertainty(u_syst, u_movbed, u_meas, u_ens, u_badcell, u_top, u_bot, u_left, u_right, cov_68):
        """Combined the uncertainty for each transect and for the measurement

        Parameters
        ----------
        u_syst: list
            List of system uncertainties for each transect
        u_movbed: list
            List of moving-bed uncertainties for each transect
        u_meas: list
            List of uncertainties for the measured portion for each transect
        u_ens: list
            List of uncertainties due to number of ensembles in each transect
        u_badcell: list
            List of uncertainties due to invalid cells and ensembles in each transect
        u_top: list
            List of uncertainties due to top extrapolation in each transect
        u_bot: list
            List of uncertainties due to the bottom extrapolation in each transect
        u_left: list
            List of uncertainties due to the left edge discharge in each transect
        u_right: list
            List of uncertainties due to the right edge discharge in each transect
        cov_68: float
            Coefficient of variation for all transects

        Returns
        -------
        u_combined_by_transect
        u_total_by_transect
        u_total_95
        :
        """

        # Create a Dataframe with all computed uncertainty for each checked transect
        u = pd.DataFrame(columns=['u_meas', 'u_movbed', 'u_syst', 'u_ens', 'u_badcell', 'u_top', 'u_bot', 'u_left',
                                  'u_right', 'u_cov'])
        u['u_syst'] = u_syst
        u['u_movbed'] = u_movbed
        u['u_meas'] = u_meas  # the only purely random uncertainty component source
        u['u_ens'] = u_ens
        u['u_badcell'] = u_badcell
        u['u_top'] = u_top
        u['u_bot'] = u_bot
        u['u_left'] = u_left
        u['u_right'] = u_right
        u['u_cov'] = cov_68

        # dsm computations without use of cov
        u_dsm = u.drop(['u_cov'], axis=1)
        u2_dsm = u_dsm ** 2
        u2_meas_dsm = u2_dsm.mean(axis=0).to_frame().T
        u_dsm['total'] = (u2_dsm.sum(axis=1) ** 0.5)
        u_dsm['total_95'] = u_dsm['total'] * 2
        u_dsm = u_dsm * 100
        u2_random_dsm = u2_meas_dsm['u_meas']
        u2_bias_dsm = u2_meas_dsm.drop(['u_meas'], axis=1).sum(axis=1)
        u2_meas_dsm['total'] = (1 / len(u_ens)) * u2_random_dsm + u2_bias_dsm[0]
        u_meas_dsm = u2_meas_dsm ** 0.5
        u_meas_dsm['total_95'] = u_meas_dsm['total'] * 2
        u_meas_dsm = u_meas_dsm * 100

        # Convert uncertainty (68% level of confidence) into variance
        # Note that only variance is additive
        u2 = u ** 2
        u2_meas = u2.mean().to_frame().T
        # Combined uncertainty by transect
        # Sum of variance of each component, then sqrt, then multiply by 100 for percentage
        u['total'] = (u2.sum(axis=1) ** 0.5)
        u['total_95'] = u['total'] * 2
        u = u * 100

        # Uncertainty for the measurement
        # The only random source is from the measured area
        u2_random = u2['u_meas'].mean()

        # All other sources are systematic (mostly due to computation method and values from user)
        # TODO What about u_cov
        u2_bias = u2_meas.drop(['u_meas'], axis=1).sum(axis=1)

        # Combined all uncertainty sources
        u2_meas['total'] = (1 / len(u_ens)) * u2_random + u2_bias[0]
        u_meas = u2_meas ** 0.5
        u_meas['total_95'] = u_meas['total'] * 2
        u_meas = u_meas * 100

        return u, u_meas, u_dsm, u_meas_dsm

        # # Add coeff of variation only if larger than the combined uncertainty
        # if (self.cov_68 - u_combined_total) > 0:
        #     print("Adding coefficient of variation")
        #     u['u_cov'] = 0.01 * self.cov_68
        #     u2 = u.applymap(lambda x: x ** 2)
        #     self.u_combined_by_transect = [100 * (x ** 0.5) for x in list(u2.sum(axis=1))]
        #     self.u_total_by_transect = [2 * x for x in self.u_combined_by_transect]
        #     u2_alea = u2['u_meas'].mean()
        #     u2_syst = list(u2.drop(['u_meas'], axis=1).mean())
        #     u2_c_gauging = (1 / self.nb_transects) * u2_alea + sum(u2_syst)
        #     u_combined_total = 100 * (u2_c_gauging ** 0.5)
        #     u_total_95 = 2 * u_combined_total
        #
        # if self.u_cov_68_user is not None:
        #     u['u_cov'] = 0.01 * self.u_cov_68_user
        #     u2 = u.applymap(lambda x: x ** 2)
        #     self.u_combined_by_transect = [100 * (x ** 0.5) for x in list(u2.sum(axis=1))]
        #     self.u_total_by_transect = [2 * x for x in self.u_combined_by_transect]
        #     u2_alea = u2['u_meas'].mean()
        #     u2_syst = list(u2.drop(['u_meas'], axis=1).mean())
        #     u2_c_gauging = (1 / self.nb_transects) * u2_alea + sum(u2_syst)
        #     u_combined_total = 100 * (u2_c_gauging ** 0.5)
        #     u_total_95 = 2 * u_combined_total

        # Average of each terms
        # Average contribution to the combined uncertainty
        # Measured uncertainty then other uncertainty sources
        # u_terms = []
        # contrib_terms_total = []
        # TODO why should the user value not be divided by number of transects
        # if self.u_meas_mean_user is not None:
        #     u_terms.append(self.u_meas_mean_user)
        #     contrib_terms_total.append(100 * ( ((0.01 * self.u_meas_mean_user) ** 2) ) / u2_c_gauging)
        # else:
        #     u_terms.append(100 * ((1 / self.nb_transects) * u2['u_meas'].mean()) ** 0.5)
        #     contrib_terms_total.append(100 * ((1 / self.nb_transects) * u2['u_meas'].mean()) / u2_c_gauging)
        # u_terms = u_terms + [100 * x ** 0.5 for x in u2_syst]
        # contrib_terms_total = contrib_terms_total + [100 * x / u2_c_gauging for x in u2_syst]
        #
        # # Store results : reordering so that syst, moving bed and measured are the three first sources
        # self.u_terms = [u_terms[i] for i in [2, 1, 0, 3, 4, 5, 6, 7, 8, 9, 10]]
        # self.u_combined_total = u_combined_total
        # self.u_total_95 = u_total_95
        # self.variance_terms_by_transect = u2
        # self.contrib_terms_total = [contrib_terms_total[i] for i in [2, 1, 0, 3, 4, 5, 6, 7, 8, 9, 10]]
        # self.contrib_legend = list(u.columns)

        # Convert relative uncertainties in m3/s and relative variance in m6/s2
        # self.u_syst_mean_abs = self.u_syst_mean*np.mean(self.sim_original['q_total'])
        # self.u_combined_by_transect_abs = np.asarray(self.u_combined_by_transect) * np.asarray(self.sim_original['q_total']) * 0.01
        # self.u_terms_abs = np.asarray(self.u_terms)*0.01*np.mean(self.sim_original['q_total'])
        # self.u_combined_total_abs = 0.01*self.u_combined_total*np.mean(self.sim_original['q_total'])
        # self.u_total_by_transect_abs = np.asarray(self.u_total_by_transect) * np.asarray(self.sim_original['q_total']) * 0.01
        # self.u_total_95_abs = 0.01*self.u_total_95*np.mean(self.sim_original['q_total'])
        # self.variance_terms_by_transect_abs=np.transpose(np.transpose(self.variance_terms_by_transect) * np.asarray(self.sim_original['q_total']) ** 2)

    def transect_extrap_data_prep(self, meas):
        """Determine checked transects and max and min exponents for power and no slip extrapolation.

        Parameters
        ----------
        meas: MeasurementData
            Object of MeasurementData
        """

        # Use only checked transects
        # Extract data that are used later on (PP and NS exponents)
        for n in range(len(meas.transects)):
            if meas.transects[n].checked:
                self.checked_idx.append(n)

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

        self.nb_transects = len(self.checked_idx)

    def run_oursin_simulations(self, meas, exp_pp_min_user, exp_pp_max_user, exp_ns_min_user, exp_ns_max_user,
                               draft_error_user, d_right_error_prct_user, d_left_error_prct_user):
        """Compute discharges (top, bot, right, left, total, middle)  based on possible scenarios

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
        """

        # If list have not be saved recompute q_sensitivity
        if not hasattr(meas.extrap_fit.q_sensitivity, 'q_pp_list'):
            meas.extrap_fit.q_sensitivity.populate_data(meas.transects, meas.extrap_fit.sel_fit)

        # Simulation original
        self.sim_orig(meas)

        # Simulation power / power default 1/6
        self.sim_extrap_pp_16['q_total'] = meas.extrap_fit.q_sensitivity.q_pp_list
        self.sim_extrap_pp_16['q_top'] = meas.extrap_fit.q_sensitivity.q_top_pp_list
        self.sim_extrap_pp_16['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_pp_list

        # Simulations power / power optimized
        self.sim_pp_min_max(meas=meas,
                        exp_pp_min_user=exp_pp_min_user,
                        exp_pp_max_user=exp_pp_max_user)

        # Simulation cns default 1/6
        self.sim_extrap_cns_16['q_total'] = meas.extrap_fit.q_sensitivity.q_cns_list
        self.sim_extrap_cns_16['q_top'] = meas.extrap_fit.q_sensitivity.q_top_cns_list
        self.sim_extrap_cns_16['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_cns_list

        # Simulation cns optimized
        self.sim_cns_min_max(meas=meas,
                         exp_ns_min_user=exp_ns_min_user,
                         exp_ns_max_user=exp_ns_max_user)

        # Simulation 3pt no slip default 1/6
        self.sim_extrap_3pns_16['q_total'] = meas.extrap_fit.q_sensitivity.q_3p_ns_list
        self.sim_extrap_3pns_16['q_top'] = meas.extrap_fit.q_sensitivity.q_top_3p_ns_list
        self.sim_extrap_3pns_16['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_3p_ns_list

        # Simulation 3pt no slip optimized
        self.sim_extrap_3pns_opt['q_total'] = meas.extrap_fit.q_sensitivity.q_3p_ns_opt_list
        self.sim_extrap_3pns_opt['q_top'] = meas.extrap_fit.q_sensitivity.q_top_3p_ns_opt_list
        self.sim_extrap_3pns_opt['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_3p_ns_opt_list

        # Simulations edge min and max
        self.sim_edge_min_max(meas=meas,
                              d_left_error_prct_user=d_left_error_prct_user,
                              d_right_error_prct_user=d_right_error_prct_user)

        # Simulation draft min and max
        self.sim_draft_max_min(meas=meas,
                               draft_error_user=draft_error_user)

        # Simulation of invalid cells and ensembles
        self.sim_invalid_cells(meas=meas)

    def measured_area_uncertainty(self, meas, u_meas_mean_user=None):
        """Compute the uncertainty related to the measured area.

        Parameters
        ----------
        meas: Measurement
            Object of class Measurement
        u_meas_mean_user: float
            User provided uncertainty of the measured area in percent
        """

        # Set uncertainty of cell size
        self.u_prct_dzi = 0.5 * 0.01  # k=1 0.5%

        # Compute the uncertainty due to the measured area
        for ind_transect in self.checked_idx:
            # Relative depth error due to vertical velocity of boat
            # TODO this does not below in the measured area, only affects bottom and edges
            relative_error_depth = self.depth_error_boat_motion(meas.transects[ind_transect])

            # Relative standard deviation of error velocity (Water Track)
            std_ev_wt_ens = self.water_std_by_error_velocity(meas.transects[ind_transect])

            # Relative standard deviation of error velocity (Bottom Track)
            std_ev_bt = self.boat_std_by_error_velocity(meas.transects[ind_transect])

            # Computation of u_meas
            q_2_tran = meas.discharge[ind_transect].total ** 2
            q_2_ens = meas.discharge[ind_transect].middle_ens ** 2
            n_cell_ens = meas.transects[ind_transect].w_vel.cells_above_sl.sum(axis=0)  # number of cells by ens
            n_cell_ens = np.where(n_cell_ens == 0, np.nan, n_cell_ens)

            # Variance for each ensembles
            u_2_meas = q_2_ens * (relative_error_depth ** 2 + std_ev_bt ** 2 +
                                  (1 / n_cell_ens) * (std_ev_wt_ens ** 2 + self.u_prct_dzi ** 2))
            # TODO DSM I would have computed as follows
            # u_2_meas = q_2_ens * (std_ev_bt ** 2 + (1 / n_cell_ens) * (std_ev_wt_ens ** 2 + u_prct_dzi ** 2))

            u_2_prct_meas = np.nansum(u_2_meas) / q_2_tran

            # Standard deviation
            u_prct_meas = u_2_prct_meas ** 0.5
            self.u_meas_list.append(u_prct_meas)

            # Compute the contribution of all terms to u_meas (sum of a0 to g0 =1)
            u_contrib_errv_v_boat = (np.nan_to_num(q_2_ens * (std_ev_bt ** 2)).sum() / q_2_tran) / u_2_prct_meas
            u_contrib_verv_h_depth = (np.nan_to_num(q_2_ens * (relative_error_depth ** 2)).sum()
                                      / q_2_tran) / u_2_prct_meas
            u_contrib_errv_v_wate = (np.nan_to_num(q_2_ens * ((1 / n_cell_ens) * (std_ev_wt_ens ** 2))).sum()
                                     / q_2_tran) / u_2_prct_meas
            u_contrib_meas_u_dzi = (np.nan_to_num(q_2_ens * ((1 / n_cell_ens) * (self.u_prct_dzi ** 2))).sum()
                                    / q_2_tran) / u_2_prct_meas

            self.u_contrib_errv_v_boat.append(u_contrib_errv_v_boat)
            self.u_contrib_verv_h_depth.append(u_contrib_verv_h_depth)
            self.u_contrib_errv_v_wate.append(u_contrib_errv_v_wate)
            self.u_contrib_meas_u_dzi.append(u_contrib_meas_u_dzi)

        # Assume 0.5% uncertainty on cell size
        if u_meas_mean_user is not None:
            self.u_meas_mean_user_list = [0.01 * u_meas_mean_user] * self.nb_transects
            self.u_meas_mean_user = u_meas_mean_user
        else:
            self.u_meas_mean_user_list = self.u_meas_list

    def compute_moving_bed_uncertainty(self, meas, u_movbed_user):
        """Computes the moving-bed uncertainty

        Parameters
        ----------
        meas: MeasurementData
            Object of MeasurementData
        u_movbed_user: float
            User provided moving-bed uncertainty in percent
        """

        self.u_movbed_list = [0.01 * meas.uncertainty.moving_bed_95 / 2] * self.nb_transects

        if u_movbed_user is not None:
            self.u_movbed_user_list = [u_movbed_user * 0.01] * self.nb_transects
            self.u_movbed_user = u_movbed_user
        else:
            self.u_movbed_user_list = self.u_movbed_list

    def compute_systematic_uncertainty(self, u_syst_mean_user):
        """Compute systematic uncertaint

        Parameters
        ----------
        u_syst_mean_user: float
            User provided systematic uncertainty in percent
        """

        self.u_syst_list = [0.01 * 1.31] * self.nb_transects

        if u_syst_mean_user is not None:
            self.u_syst_mean_user_list = [u_syst_mean_user * 0.01] * self.nb_transects
            self.u_syst_mean_user = u_syst_mean_user
        else:
            self.u_syst_mean_user_list = self.u_syst_list

    def compute_number_ensembles_uncertainty(self, meas, u_ens_user):
        """Computes the uncertainty due to the number of ensembles in a transect.

        Parameters
        ----------
        meas: MeasurementData
            Object of MeasurementData
        u_ens_user: float
            User provided uncertianty in percent
        """

        for trans_id in self.checked_idx:
            # Compute uncertainty due to limited number of ensembles (ISO 748; Le Coz et al., 2012)
            self.u_ens_list.append(0.01 * 32 * len(meas.discharge[trans_id].middle_ens) ** (-0.88))

        if u_ens_user is not None:
            self.u_ens_user_list = [0.01 * u_ens_user] * self.nb_transects
            self.u_ens_user = u_ens_user
        else:
            self.u_ens_user_list = self.u_ens_list

    def compute_meas_cov(self, meas, u_cov_68_user):
        """Compute the coefficient of variation of the total transect discharges used in the measurement.

        Parameters
        ----------
        meas: MeasurementData
            Object of MeasurementData
        u_cov_68_user: float
            User provided coefficient of variation
        """

        self.cov_68 = np.nan
        nb_transects = len(meas.transects)

        # Only compute for multiple transects
        if nb_transects > 1:
            total_q = []
            for n in range(nb_transects):
                if meas.transects[n].checked:
                    total_q.append(meas.discharge[n].total)

            # Compute coefficient of variation
            cov = np.abs(np.nanstd(total_q, ddof=1) / np.nanmean(total_q))

            # Inflate the cov to the 95% value
            if len(total_q) == 2:
                # Use the approximate method as taught in class to reduce the high coverage factor for 2 transects
                # and account for prior knowledge related to 720 second duration analysis
                cov_95 = cov * 0.033
                self.cov_68 = cov_95 / 2
            else:
                # Use Student's t to inflate COV for n > 2
                cov_95 = t.interval(0.95, len(total_q) - 1)[1] * cov / len(total_q) ** 0.5
                self.cov_68 = cov_95 / 2

        if u_cov_68_user is not None:
            self.u_cov_68_user = u_cov_68_user * 0.01
            self.u_cov_68_user_value = self.u_cov_68_user
        else:
            self.u_cov_68_user_value = self.cov_68

    def sim_orig(self, meas):
        """Stores original measurement results in a data frame

        Parameters
        ----------
        meas: MeasurementData
            Object of MeasurementData
        """
        transect_q=dict()
        for trans_id in self.checked_idx:
            transect_q['q_total'] = meas.discharge[trans_id].total
            transect_q['q_top'] = meas.discharge[trans_id].top
            transect_q['q_bot'] = meas.discharge[trans_id].bottom
            transect_q['q_right'] = meas.discharge[trans_id].right
            transect_q['q_left'] = meas.discharge[trans_id].left
            transect_q['q_middle'] = meas.discharge[trans_id].middle
            self.sim_original = self.sim_original.append(transect_q, ignore_index=True, sort=False)

    def sim_cns_min_max(self, meas, exp_ns_min_user, exp_ns_max_user):
        """Computes simulations resulting in the the min and max discharges for a constant no slip extrapolation
        fit.

        Parameters
        ----------
        meas: MeasurementData
            Object of MeasurementData
        exp_ns_min_user: float
            User supplied minimum exponent for the no slip fit
        exp_ns_max_user: float
            User supplied minimum exponet for the no slip fit
        """

        # Compute min-max no slip exponent
        skip_ns_min_max, self.exp_ns_max, self.exp_ns_min = self.compute_ns_max_min(meas=meas,
                                                                                    ns_exp=self.ns_exp,
                                                                                    exp_ns_min_user=exp_ns_min_user,
                                                                                    exp_ns_max_user=exp_ns_max_user)

        # Optimized
        self.sim_extrap_cns_opt['q_total'] = meas.extrap_fit.q_sensitivity.q_cns_opt_list
        self.sim_extrap_cns_opt['q_top'] = meas.extrap_fit.q_sensitivity.q_top_cns_opt_list
        self.sim_extrap_cns_opt['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_cns_opt_list

        # Max min
        if skip_ns_min_max:
            # If cns not used both max and min are equal to the optimized value
            self.sim_extrap_cns_min['q_total'] = meas.extrap_fit.q_sensitivity.q_cns_opt_list
            self.sim_extrap_cns_min['q_top'] = meas.extrap_fit.q_sensitivity.q_top_cns_opt_list
            self.sim_extrap_cns_min['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_cns_opt_list
            self.sim_extrap_cns_max['q_total'] = meas.extrap_fit.q_sensitivity.q_cns_opt_list
            self.sim_extrap_cns_max['q_top'] = meas.extrap_fit.q_sensitivity.q_top_cns_opt_list
            self.sim_extrap_cns_max['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_cns_opt_list
        else:
            # Compute q for min and max values
            q = QComp()
            for trans_id in self.checked_idx:
                # Compute min values
                q.populate_data(data_in=meas.transects[trans_id],
                                top_method='Constant',
                                bot_method='No Slip',
                                exponent=self.exp_ns_min)
                self.sim_extrap_cns_min.loc[len(self.sim_extrap_cns_min)] = [q.total, q.top, q.bottom]
                # Compute max values
                q.populate_data(data_in=meas.transects[trans_id],
                                top_method='Constant',
                                bot_method='No Slip',
                                exponent=self.exp_ns_max)
                self.sim_extrap_cns_max.loc[len(self.sim_extrap_cns_max)] = [q.total, q.top, q.bottom]

    def sim_pp_min_max(self, meas, exp_pp_min_user, exp_pp_max_user):
        """Computes simulations resulting in the the min and max discharges for a power power extrapolation
        fit.

        Parameters
        ----------
        meas: MeasurementData
            Object of MeasurementData
        exp_pp_min_user: float
            User supplied minimum exponent for the power fit
        exp_pp_max_user: float
            User supplied minimum exponet for the power fit
                """
        # Compute min-max power exponent
        skip_pp_min_max, self.exp_pp_max, self.exp_pp_min = self.compute_pp_max_min(meas=meas,
                                                                                    exp_95ic_min=self.exp_95ic_min,
                                                                                    exp_95ic_max=self.exp_95ic_max,
                                                                                    pp_exp=self.pp_exp,
                                                                                    exp_pp_min_user=exp_pp_min_user,
                                                                                    exp_pp_max_user=exp_pp_max_user)

        # Optimized
        self.sim_extrap_pp_opt['q_total'] = meas.extrap_fit.q_sensitivity.q_pp_opt_list
        self.sim_extrap_pp_opt['q_top'] = meas.extrap_fit.q_sensitivity.q_top_pp_opt_list
        self.sim_extrap_pp_opt['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_pp_opt_list

        # Max min
        if skip_pp_min_max:
            self.sim_extrap_pp_min['q_total'] = meas.extrap_fit.q_sensitivity.q_pp_opt_list
            self.sim_extrap_pp_min['q_top'] = meas.extrap_fit.q_sensitivity.q_top_pp_opt_list
            self.sim_extrap_pp_min['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_pp_opt_list
            self.sim_extrap_pp_max['q_total'] = meas.extrap_fit.q_sensitivity.q_pp_opt_list
            self.sim_extrap_pp_max['q_top'] = meas.extrap_fit.q_sensitivity.q_top_pp_opt_list
            self.sim_extrap_pp_max['q_bot'] = meas.extrap_fit.q_sensitivity.q_bot_pp_opt_list
        else:
            q = QComp()
            for trans_id in self.checked_idx:
                q.populate_data(data_in=meas.transects[trans_id],
                                top_method='Power',
                                bot_method='Power',
                                exponent=self.exp_pp_min)
                self.sim_extrap_pp_min.loc[len(self.sim_extrap_pp_min)] = [q.total, q.top, q.bottom]

                q.populate_data(data_in=meas.transects[trans_id],
                                top_method='Power',
                                bot_method='Power',
                                exponent=self.exp_pp_max)
                self.sim_extrap_pp_max.loc[len(self.sim_extrap_pp_max)] = [q.total, q.top, q.bottom]

    def sim_edge_min_max(self, meas, d_left_error_prct_user, d_right_error_prct_user):
        """Computes simulations for the maximum and minimum edge discharges.

        Parameters
        ----------
        meas: MeasurementData
            Object of measurement data
        d_left_error_prct_user: float
            Percent error for the left edge distance provided by the user
        d_right_error_prct_user: float
            Percent error for the right edge distance provided by the user
        """

        # Create measurement copy to allow changes without affecting original
        meas_temp = copy.deepcopy(meas)

        # Process each checked transect
        for trans_id in self.checked_idx:
            # Compute max and min edge distances
            max_left_dist, max_right_dist, min_left_dist, min_right_dist = \
                self.compute_edge_dist_max_min(transect=meas.transects[trans_id],
                                               d_left_error_prct_user=d_left_error_prct_user,
                                               d_right_error_prct_user=d_right_error_prct_user)

            # Compute edge minimum
            self.d_right_error_min.append(min_right_dist)
            self.d_left_error_min.append(min_left_dist)
            meas_temp.transects[trans_id].edges.left.distance_m = min_left_dist
            meas_temp.transects[trans_id].edges.right.distance_m = min_right_dist
            meas_temp.transects[trans_id].edges.left.type = 'Triangular'
            meas_temp.transects[trans_id].edges.right.type = 'Triangular'
            meas_temp.discharge[trans_id].populate_data(data_in=meas_temp.transects[trans_id],
                                                         moving_bed_data=meas_temp.mb_tests)
            self.sim_edge_min.loc[len(self.sim_edge_min)] = [meas_temp.discharge[trans_id].total,
                                                             meas_temp.discharge[trans_id].left,
                                                             meas_temp.discharge[trans_id].right]

            # Compute edge maximum
            self.d_right_error_max.append(max_right_dist)
            self.d_left_error_max.append(max_left_dist)
            meas_temp.transects[trans_id].edges.left.distance_m = max_left_dist
            meas_temp.transects[trans_id].edges.right.distance_m = max_right_dist
            meas_temp.transects[trans_id].edges.left.type = 'Rectangular'
            meas_temp.transects[trans_id].edges.right.type = 'Rectangular'
            meas_temp.discharge[trans_id].populate_data(data_in=meas_temp.transects[trans_id],
                                                         moving_bed_data=meas_temp.mb_tests)
            self.sim_edge_max.loc[len(self.sim_edge_max)] = [meas_temp.discharge[trans_id].total,
                                                             meas_temp.discharge[trans_id].left,
                                                             meas_temp.discharge[trans_id].right]

    def sim_draft_max_min(self, meas, draft_error_user):
        """Compute the simulations for the max and min draft errror.

        Parameters
        ----------
        meas: MeasurementData
            Object of MeasurementData
        draft_error_user: float
            User supplied draft error in m
        """
        # Create copy of meas to avoid changing original
        meas_temp = copy.deepcopy(meas)

        for trans_id in self.checked_idx:
            # Compute max and min draft
            draft_max, draft_min, draft_error = self.compute_draft_max_min(transect=meas.transects[trans_id],
                                                                           draft_error_user=draft_error_user)
            self.list_draft_error.append(draft_error)

            # Compute discharge for draft min
            meas_temp.transects[trans_id].change_draft(draft_min)
            meas_temp.discharge[trans_id].populate_data(data_in=meas_temp.transects[trans_id],
                                                         moving_bed_data=meas_temp.mb_tests)
            self.sim_draft_min.loc[len(self.sim_draft_min)] = [meas_temp.discharge[trans_id].total,
                                                               meas_temp.discharge[trans_id].top,
                                                               meas_temp.discharge[trans_id].left,
                                                               meas_temp.discharge[trans_id].right]
            # Compute discharge for draft max
            meas_temp.transects[trans_id].change_draft(draft_max)
            meas_temp.discharge[trans_id].populate_data(data_in=meas_temp.transects[trans_id],
                                                         moving_bed_data=meas_temp.mb_tests)
            self.sim_draft_max.loc[len(self.sim_draft_max)] = [meas_temp.discharge[trans_id].total,
                                                               meas_temp.discharge[trans_id].top,
                                                               meas_temp.discharge[trans_id].left,
                                                               meas_temp.discharge[trans_id].right]

    def sim_invalid_cells(self, meas):
        """Computes simulations using different methods to interpolate for invalid cells and ensembles.

        Parameters
        ----------
        meas: MeasurementData
            Object of MeasurementData
        """

        # Simulations for invalid cells and ensembles
        meas_temp = copy.deepcopy(meas)
        for trans_id in self.checked_idx:
            # TRDI method
            meas_temp.transects[trans_id].w_vel.interpolate_cells_trdi(meas_temp.transects[trans_id])
            meas_temp.discharge[trans_id].populate_data(data_in=meas_temp.transects[trans_id],
                                                         moving_bed_data=meas_temp.mb_tests)
            self.sim_cells_trdi.loc[len(self.sim_cells_trdi)] = [meas_temp.discharge[trans_id].total,
                                                                     meas_temp.discharge[trans_id].middle]

            # Above only
            meas_temp.transects[trans_id].w_vel.interpolate_abba(meas_temp.transects[trans_id], search_loc=['above'])
            meas_temp.discharge[trans_id].populate_data(data_in=meas_temp.transects[trans_id],
                                                         moving_bed_data=meas_temp.mb_tests)
            self.sim_cells_above.loc[len(self.sim_cells_above)] = [meas_temp.discharge[trans_id].total,
                                                                 meas_temp.discharge[trans_id].middle]
            # Below only
            meas_temp.transects[trans_id].w_vel.interpolate_abba(meas_temp.transects[trans_id], search_loc=['below'])
            meas_temp.discharge[trans_id].populate_data(data_in=meas_temp.transects[trans_id],
                                                         moving_bed_data=meas_temp.mb_tests)
            self.sim_cells_below.loc[len(self.sim_cells_below)] = [meas_temp.discharge[trans_id].total,
                                                                   meas_temp.discharge[trans_id].middle]
            # Before only
            meas_temp.transects[trans_id].w_vel.interpolate_abba(meas_temp.transects[trans_id], search_loc=['before'])
            meas_temp.discharge[trans_id].populate_data(data_in=meas_temp.transects[trans_id],
                                                         moving_bed_data=meas_temp.mb_tests)
            self.sim_cells_before.loc[len(self.sim_cells_before)] = [meas_temp.discharge[trans_id].total,
                                                                     meas_temp.discharge[trans_id].middle]
            # After only
            meas_temp.transects[trans_id].w_vel.interpolate_abba(meas_temp.transects[trans_id], search_loc=['after'])
            meas_temp.discharge[trans_id].populate_data(data_in=meas_temp.transects[trans_id],
                                                         moving_bed_data=meas_temp.mb_tests)
            self.sim_cells_after.loc[len(self.sim_cells_after)] = [meas_temp.discharge[trans_id].total,
                                                                   meas_temp.discharge[trans_id].middle]

    @staticmethod
    def compute_draft_max_min(transect, draft_error_user=None):
        """Determine the max and min values of the ADCP draft.
        """
        depths = transect.depths.bt_depths.depth_processed_m  # depth by ens
        depth_90 = np.quantile(depths, q=0.9)  # quantile 90% to avoid spikes

        # Determine draft error value
        if draft_error_user is None:
            if depth_90 < 2.50:
                draft_error = 0.02
            else:
                draft_error = 0.05
        else:
            draft_error = draft_error_user

        # Compute draft max and min
        draft_min = transect.depths.bt_depths.draft_orig_m - draft_error
        draft_max = transect.depths.bt_depths.draft_orig_m + draft_error

        if draft_min <=0:
            draft_min = 0.01

        return draft_max, draft_min, draft_error

    @staticmethod
    def compute_edge_dist_max_min(transect, d_left_error_prct_user, d_right_error_prct_user):
        """Compute the max and min edge distances.
        """

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

        # Compute max distance for both edges
        max_left_dist = (1 + d_left_error_prct) * init_dist_left
        max_right_dist = (1 + d_right_error_prct) * init_dist_right

        return max_left_dist, max_right_dist, min_left_dist, min_right_dist

    @staticmethod
    def compute_pp_max_min(meas, exp_95ic_min, exp_95ic_max, pp_exp, exp_pp_min_user, exp_pp_max_user):
        """Determine the max and min exponents for power fit.
        """
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

        return skip_PP_min_max, exp_pp_max, exp_pp_min

    @staticmethod
    def compute_ns_max_min(meas, ns_exp, exp_ns_min_user=None, exp_ns_max_user=None ):
        """Determine the max and min no slip exponents.
        """
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

        return skip_NS_min_max, exp_ns_max, exp_ns_min

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
        d_vel_filtered = np.tile([np.nan], transect.w_vel.d_mps.shape)
        d_vel_filtered[transect.w_vel.valid_data[0]] = transect.w_vel.d_mps[transect.w_vel.valid_data[0]]

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

        Parameters
        ----------
        transect: TransectData
            Object of TransectData

        Returns
        -------
        std_ev_BT: float
            Standard devation of bottom track error velocity
        """

        # Compute boat speed
        u_boat = transect.boat_vel.bt_vel.u_processed_mps
        v_boat = transect.boat_vel.bt_vel.v_processed_mps
        speed = np.sqrt(u_boat ** 2 + v_boat ** 2)

        # Use only valid error velocity data
        d_vel_filtered = np.tile([np.nan], transect.boat_vel.bt_vel.d_mps.shape)
        d_vel_filtered[transect.boat_vel.bt_vel.valid_data[0]] = \
            transect.boat_vel.bt_vel.d_mps[transect.boat_vel.bt_vel.valid_data[0]]

        # Compute relative standard deviation of error velocity
        all_std_ev_BT = np.nanstd(d_vel_filtered)
        std_ev_BT = np.abs(all_std_ev_BT) / speed
        # TODO Consider substituting the overal std for nan rather than 0
        # std_ev_BT[np.isnan(std_ev_BT)] = all_std_ev_BT
        std_ev_BT[np.isnan(std_ev_BT)] = 0.00

        return std_ev_BT

    @staticmethod
    def apply_u_rect(list_sims, col_name):
        # Compute the uncertainty using list of simulated discharges following a ranctangular law
        # simu = pd.DataFrame()
        # for i in range(len(list_simu)):
        #     name_col = 'simu' + str(i)
        #     simu[name_col] = list_simu[i]
        vertical_stack = pd.concat(list_sims, axis=0, sort=True)
        u_rect = (vertical_stack.groupby(vertical_stack.index)[col_name].max()
                  - vertical_stack.groupby(vertical_stack.index)[col_name].min()) / (2 * (3 ** 0.5))

        return (u_rect)

    # def plot_u_meas_contrib(self, plot=False, name_plot_u_meas='Contrib_u_meas.png'):
    #     """
    #     Plot a barplot showing the contribution of uncertainty terms to the measured uncertainty
    #
    #     :param plot:
    #         if True save the barplot
    #     :param name_plot_u_meas:
    #         name of the file to be saved if plot is True
    #     :return:
    #     """
    #     # ----- Store in dataframe
    #     Contrib_meas = pd.DataFrame()
    #     Contrib_meas['v_boat'] = self.u_contrib_meas_v_boat
    #     Contrib_meas['error_vel_boat'] = self.u_contrib_errv_v_boat
    #     Contrib_meas['depth vertical_vel_boat'] = self.u_contrib_verv_h_depth
    #     Contrib_meas['error_vel_water'] = self.u_contrib_errv_v_wate
    #     Contrib_meas['v_water'] = self.u_contrib_meas_v_wate
    #     Contrib_meas['cell size'] = self.u_contrib_meas_u_dzi
    #     Contrib_meas_prct = 100 * Contrib_meas  # Convert into percentage
    #
    #     # ----- Plot
    #     plt.rcParams.update({'font.size': 14})
    #     Contrib_meas_prct.plot.bar(stacked=True, figsize=(10, 7))
    #     plt.xlabel('Transect index')
    #     plt.grid(True, linestyle='--', axis='y')
    #     plt.ylabel('Contribution to $u_{meas}$ uncertainty [%]')
    #
    #     if self.u_meas_mean_user is not None:
    #         plt.legend(title=" WARNING ! \n $u_{meas}$ has been \n modified by the user", labels=[],
    #                    shadow=False, framealpha=1,
    #                    title_fontsize=40,
    #                    loc="center",
    #                    bbox_to_anchor=(0.5, 0.5))
    #     else:
    #         plt.legend(title="Error sources",
    #                loc="center left",
    #                labelspacing=-2.1,
    #                frameon=False,
    #                bbox_to_anchor=(1, 0.5))
    #
    #     # ---- If plot is True save the plot
    #     if plot:
    #         plt.savefig(name_plot_u_meas, bbox_inches='tight')
    #     plt.show()
    #
    # def plot_u_contrib(self, plot=False, name_plot_u_contrib='Contrib_u.png'):
    #     """
    #     Plot a barplot showing the contribution in terms of variance
    #     of each uncertainty component for each transect
    #
    #     :param plot:
    #         if True save the plot in a file
    #     :param name_plot_u_contrib:
    #         name of the file to be saved if plot is True
    #     :return: barplot
    #     """
    #     # --- Variance in m6/s2
    #     Contrib_all = self.variance_terms_by_transect_abs  # m6/s2
    #     list_basic_color_oursin = [u'#d62728', u'#7f7f7f', u'#ff7f0e', 'gold',
    #                                u'#bcbd22', u'#2ca02c', u'#e377c2',
    #                                u'#8c564b', u'#17becf', u'#1f77b4', u'#9467bd']
    #     # ----- Plot
    #     plt.rcParams.update({'font.size': 14})
    #     Contrib_all.plot.bar(stacked=True, color=list_basic_color_oursin, figsize=(10, 7))
    #     plt.xlabel('Transect index')
    #     plt.grid(True, linestyle='--', axis='y')
    #     # plt.ylabel('Sum of variance [%]')
    #     plt.ylabel(r'Variance [$m^6/s^{-2}$]')
    #     plt.legend(title="Uncertainty components",
    #                loc="center left",
    #                labelspacing=-2.1,
    #                frameon=False,
    #                bbox_to_anchor=(1, 0.5))
    #
    #     plt.title("U(Q) = " + str('%.1f' % self.u_total_95) +
    #               "% PP: " + str('%.2f' % self.exp_pp_min) +
    #               "-" + str('%.2f' % self.exp_pp_max) + " NS: " +
    #               str('%.2f' % self.exp_ns_min) + "-" +
    #               str('%.2f' % self.exp_ns_max))
    #
    #
    #
    #     # ---- If plot is True save the plot
    #     if plot:
    #         plt.savefig(name_plot_u_contrib, bbox_inches='tight')
    #     plt.show()
    #
    # def plot_u_contrib_relative(self, plot=False, name_plot_u_contrib='Contrib_u.png'):
    #     """
    #     Plot a barplot showing the contribution in terms of variance
    #     of each uncertainty component for each transect
    #
    #     :param plot:
    #         if True save the plot in a file
    #     :param name_plot_u_contrib:
    #         name of the file to be saved if plot is True
    #     :return: barplot
    #     """
    #     # --- Variance in m6/s2
    #     Contrib_all = 100*100*self.variance_terms_by_transect  # m6/s2
    #     list_basic_color_oursin = [u'#d62728', u'#7f7f7f', u'#ff7f0e', 'gold',
    #                                u'#bcbd22', u'#2ca02c', u'#e377c2',
    #                                u'#8c564b', u'#17becf', u'#1f77b4', u'#9467bd']
    #     # ----- Plot
    #     plt.rcParams.update({'font.size': 14})
    #     Contrib_all.plot.bar(stacked=True, color=list_basic_color_oursin, figsize=(10, 7))
    #     plt.xlabel('Transect index')
    #     plt.grid(True, linestyle='--', axis='y')
    #     plt.ylabel('Sum of variance [%]')
    #     # plt.ylabel(r'Variance [$m^6/s^{-2}$]')
    #     plt.legend(title="Uncertainty components",
    #                loc="center left",
    #                labelspacing=-2.1,
    #                frameon=False,
    #                bbox_to_anchor=(1, 0.5))
    #
    #     plt.title("U(Q) = " + str('%.1f' % self.u_total_95) +
    #               "% PP: " + str('%.2f' % self.exp_pp_min) +
    #               "-" + str('%.2f' % self.exp_pp_max) + " NS: " +
    #               str('%.2f' % self.exp_ns_min) + "-" +
    #               str('%.2f' % self.exp_ns_max))
    #
    #     # ---- If plot is True save the plot
    #     if plot:
    #         plt.savefig(name_plot_u_contrib, bbox_inches='tight')
    #     plt.show()
    #
    # def plot_u_mean_pie(self, plot=False, name_plot_u_pie='Mean_pie_u.png'):
    #     """
    #     Plot a pie showing the average contribution of each uncertainty source to the total uncertainty
    #
    #     :param plot:
    #         if True save the figure
    #     :param name_plot_u_pie:
    #         Name of the file if plot is True
    #     :return: plot
    #     """
    #     list_basic_color_oursin = [u'#d62728', u'#7f7f7f', u'#ff7f0e', 'gold',
    #                                u'#bcbd22', u'#2ca02c', u'#e377c2',
    #                                u'#8c564b', u'#17becf', u'#1f77b4', u'#9467bd']
    #
    #     def my_autopct(pct):
    #         return (str('%.1f' % pct) + '%') if pct > 2 else ''
    #
    #     u_terms = [self.u_terms[i] for i in [1, 0, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
    #     contrib_terms_total = [self.contrib_terms_total[i] for i in [1, 0, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
    #
    #     plt.rcParams.update({'font.size': 14})
    #     plt.pie(x=contrib_terms_total,
    #             colors=list_basic_color_oursin,
    #             autopct=my_autopct,  # lambda x: str(round(x, 2)) + '%',
    #             pctdistance=1.25
    #             )
    #     plt.legend(labels=[str(y) + ' = ' + str('%.1f' % x) + '%' for x, y in zip(u_terms, self.contrib_legend)],
    #                title="Uncertainty components (68% IC)",
    #                loc="center left",
    #                labelspacing=-2.1,
    #                frameon=False,
    #                bbox_to_anchor=(1, 0.5))
    #     if plot:
    #         plt.savefig(name_plot_u_pie, bbox_inches='tight')
    #     plt.show()


