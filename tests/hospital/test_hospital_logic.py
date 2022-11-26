#!/usr/bin/env python3
"""
Tests of the individual-based model, COVID19-IBM

Usage:
With pytest installed (https://docs.pytest.org/en/latest/getting-started.html) tests can be 
run by calling 'pytest' from project folder.  

Created: April 2020
Author: Dylan Feldner-Busztin
"""

import numpy as np, pandas as pd
from tests import constant
from tests import utilities as utils
from parameters import ParameterSet


class TestClass(object):
    """
    Test class for checking that the model behaves as expected with baseline parameters.
    """

    def test_hcw_in_population_list(self):
        """
        Test that healthcare worker IDs correspond to population IDs
        """

        # Adjust baseline parameter
        params = ParameterSet(constant.TEST_DATA_FILE, line_number=1)
        params.set_param("n_total", 20000)
        params.set_param("hospital_on", 1)
        params.write_params(constant.TEST_DATA_FILE)

        mparams = utils.get_params_custom()
        model  = utils.get_model_swig( mparams )
        model.run(verbose=False)
        model.write_individual_file()
        model.write_ward_data()
        
        df_hcw = pd.read_csv(constant.TEST_HCW_FILE)
        df_population = pd.read_csv(constant.TEST_INDIVIDUAL_FILE)
        hcw_idx_list = df_hcw.pdx.values
        population_idx_list = df_population.ID.values

        assert all(idx in population_idx_list for idx in hcw_idx_list)


    def test_hcw_not_in_work_network(self):
        """
        If worker type not -1 (they are a healthcare worker), then work network must be -1 (they are not in the standard work network).
        """

        # Adjust baseline parameter
        params = ParameterSet(constant.TEST_DATA_FILE, line_number=1)
        params.set_param("n_total", 20000)
        params.set_param("hospital_on", 1)
        params.set_param("days_of_interactions", 10)
        params.set_param("end_time", 20)
        params.write_params(constant.TEST_DATA_FILE)

        mparams = utils.get_params_custom()
        model  = utils.get_model_swig( mparams )
        model.run(verbose=False)
        model.write_interactions_file()
        
        df_interactions = pd.read_csv(constant.TEST_INTERACTION_FILE)

        w1_hcw_condition = df_interactions['worker_type_1'] != -1
        w1_worknetwork_condition = df_interactions['occupation_network_1'] != -1
        df_test_worker1 = df_interactions[w1_hcw_condition & w1_worknetwork_condition]

        assert len(df_test_worker1.index) == 0
        
        w2_hcw_condition = df_interactions['worker_type_2'] != -1
        w2_worknetwork_condition = df_interactions['occupation_network_2'] != -1
        df_test_worker2 = df_interactions[w2_hcw_condition & w2_worknetwork_condition]

        assert len(df_test_worker2.index) == 0

    
    def test_hcw_listed_once(self):
        """
        Test that healthcare workers IDs appear only once in the hcw file and therefore only belong to one ward/ hospital
        """

        # Adjust baseline parameter
        params = ParameterSet(constant.TEST_DATA_FILE, line_number=1)
        params.set_param("n_total", 20000)
        params.set_param("hospital_on", 1)
        params.write_params(constant.TEST_DATA_FILE)

        mparams = utils.get_params_custom()
        model  = utils.get_model_swig( mparams )
        model.run(verbose=False)
        model.write_ward_data()

        df_hcw = pd.read_csv(constant.TEST_HCW_FILE)
        hcw_idx_list = df_hcw.pdx.values

        assert len(hcw_idx_list) == len(set(hcw_idx_list))


    def test_ward_capacity(self):
        """
        Test that patients in ward do not exceed number of ward beds.
        """

        # Adjust baseline parameter
        params = ParameterSet(constant.TEST_DATA_FILE, line_number=1)
        params.set_param("n_total", 20000)
        params.set_param("hospital_on", 1)
        params.write_params(constant.TEST_DATA_FILE)

        mparams = utils.get_params_custom()
        model  = utils.get_model_swig( mparams )
        model.run(verbose=False)

        df_hcw_time_step = pd.read_csv(constant.TEST_OUTPUT_FILE_HOSPITAL_TIME_STEP)
        df_number_beds_exceeded = df_hcw_time_step.query('n_patients > n_beds')

        assert len(df_number_beds_exceeded.index) == 0


    def test_ward_duplicates(self):
        """
        Test that patients in wards not duplicated.
        """

        # Adjust baseline parameter
        params = ParameterSet(constant.TEST_DATA_FILE, line_number=1)
        params.set_param("n_total", 20000)
        params.set_param("hospital_on", 1)
        params.write_params(constant.TEST_DATA_FILE)

        mparams = utils.get_params_custom()
        model  = utils.get_model_swig( mparams )
        model.run(verbose=False)

        df_hcw_time_step = pd.read_csv(constant.TEST_OUTPUT_FILE_HOSPITAL_TIME_STEP)
        
        # Iterate over time steps
        max_time = df_hcw_time_step['time_step'].max()

        for t_step in range(max_time):

            time_df = df_hcw_time_step['time_step'] == t_step
            patient_df = df_hcw_time_step['patient_type'] == 1
            test_df = df_hcw_time_step[time_df & patient_df]
            test_df = test_df.pdx.values

            assert len(test_df) == len(set(test_df))


    def test_patients_do_not_infect_non_hcw(self):
        """
        Tests that hospital patients have only been able to infect
        hospital healthcare workers.
        """

        # Adjust baseline parameter
        params = ParameterSet(constant.TEST_DATA_FILE, line_number=1)
        params.set_param("n_total", 20000)
        params.set_param("hospital_on", 1)
        params.write_params(constant.TEST_DATA_FILE)

        mparams = utils.get_params_custom()
        model  = utils.get_model_swig( mparams )
        model.run(verbose=False)
        model.write_transmissions()

        df_transmission_output = pd.read_csv(constant.TEST_TRANSMISSION_FILE)
        infected_non_hcw = df_transmission_output["worker_type_recipient"] == constant.NOT_HEALTHCARE_WORKER
        infected_non_hcw = df_transmission_output[infected_non_hcw]
 
        # loop through infected non healthcare workers and check their infector was not a hospital patient
        for index, row in infected_non_hcw.iterrows():
            infector_hospital_state = int(row["hospital_state_source"])
            assert infector_hospital_state not in [constant.EVENT_TYPES.GENERAL.value, constant.EVENT_TYPES.ICU.value]
            

    def test_interaction_type_representative(self):
        """
        Tests that each type of interaction occurs at least once
        """

        # Adjust baseline parameter
        params = ParameterSet(constant.TEST_DATA_FILE, line_number=1)
        params.set_param("n_total", 20000)
        params.set_param("n_seed_infection", 1000)
        params.set_param("hospital_on", 1)
        params.set_param("end_time", 30)
        params.write_params(constant.TEST_DATA_FILE)

        mparams = utils.get_params_custom()
        model  = utils.get_model_swig( mparams )
        model.run(verbose=False)
        model.write_interactions_file()

        list_all_interaction_types = [constant.HOUSEHOLD,
                                    constant.OCCUPATION,
                                    constant.RANDOM,
                                    constant.HOSPITAL_WORK,
                                    constant.HOSPITAL_DOCTOR_PATIENT_GENERAL,
                                    constant.HOSPITAL_NURSE_PATIENT_GENERAL,
                                    constant.HOSPITAL_DOCTOR_PATIENT_ICU,
                                    constant.HOSPITAL_NURSE_PATIENT_ICU]

        df_interaction_output = pd.read_csv(constant.TEST_INTERACTION_FILE)

        list_this_simulation_interaction_types = df_interaction_output.type.unique()
        list_this_simulation_interaction_types.sort()

        np.testing.assert_equal( list_all_interaction_types, list_this_simulation_interaction_types)