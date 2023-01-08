#!/usr/bin/env python3
"""
Created on Fri Dec 09 05:58:00 2022
Usage:
    pytest -rf tests/test_analysis.py::TestClass::test_analysis
    from the main folder
@author: Adam Fowler <adam@adamfowler.org> <adam.fowler@spc.ox.ac.uk>
"""

import numpy as np, pandas as pd
import pytest

# import sys
# sys.path.append("src/COVID19")

from COVID19.analysis import *
from COVID19.model import *

class TestClass(object):

    def test_infector_summary_network(self):
        isn = InfectorSummaryNetwork()
        isn.addInfection(ContactEvent(1,2,3,True,5))
        isn.addInfection(ContactEvent(1,3,3,False,5))
        isn.addInfection(ContactEvent(1,4,3,False,5))

        np.testing.assert_equal(isn.getInfectedCount(),1,"Wrong infected count")
        np.testing.assert_equal(isn.getSusceptibleCount(),3,"Wrong susceptibles count")

    def test_infector_summaries(self):
        infs = InfectorSummary()
        infs.addInfection(ContactEvent(1,2,3,True,5))
        infs.addInfection(ContactEvent(1,3,3,False,5))
        infs.addInfection(ContactEvent(1,4,3,False,5))
        infs.addInfection(ContactEvent(1,5,3,False,1))
        infs.addInfection(ContactEvent(1,6,3,True,1))

        networks = infs.getNetworkIds()
        np.testing.assert_equal(len(networks),2,"Should be 2 networks")
        assert "5" in networks, "Missing network ID"
        assert "1" in networks, "Missing network ID"

        np.testing.assert_equal(infs.getInfectedCount("5"),1,"Wrong infected count")
        np.testing.assert_equal(infs.getSusceptibleCount("5"),2,"Wrong susceptible count")

        np.testing.assert_equal(infs.getInfectedCount("1"),1,"Wrong infected count")
        np.testing.assert_equal(infs.getSusceptibleCount("1"),1,"Wrong susceptible count")

        np.testing.assert_equal(infs.getAllInfectedCount(),2,"Wrong infected count")
        np.testing.assert_equal(infs.getAllSusceptibleCount(),3,"Wrong susceptible count")

    """
    Test basic summariser
    """
    def test_analysis(self):
        finalTau = 0.417

        contactEvents = []
        # Day 1 - Index case (1) infected, not infectious
        # Day 2 - Index case (1) infected, not infectious
        # Day 3 - Index case (1) infected, just become infectious
        contactEvents.append(ContactEvent(1,2,3,True,5))   # Work transmission
        contactEvents.append(ContactEvent(1,3,3,False,5))  # Work non-transmission
        contactEvents.append(ContactEvent(1,4,3,False,5))  # Work non-transmission
        contactEvents.append(ContactEvent(1,5,3,False,1))  # Home non-transmission
        contactEvents.append(ContactEvent(1,6,3,True,1))   # Home transmission
        # Day 4 - Index case (1) infected, infectious
        contactEvents.append(ContactEvent(1,2,4,False,5))  # Work non-transmission (but already infected on Day 3)
        contactEvents.append(ContactEvent(1,3,4,False,5))  # Work non-transmission
        contactEvents.append(ContactEvent(1,10,4,False,5)) # Work non-transmission
        contactEvents.append(ContactEvent(1,11,4,False,5)) # Work non-transmission
        contactEvents.append(ContactEvent(1,12,4,False,5)) # Work non-transmission
        contactEvents.append(ContactEvent(1,5,4,False,1))  # Home non-transmission
        contactEvents.append(ContactEvent(1,6,4,False,1))  # Home non-transmission (Already infected day 3)
        # Day 5 - Index case (1) infected, infectious
        contactEvents.append(ContactEvent(1,2,5,False,5))  # Work non-transmission (but already infected on Day 3)
        contactEvents.append(ContactEvent(1,3,5,False,5))  # Work non-transmission
        contactEvents.append(ContactEvent(1,10,5,False,5)) # Work non-transmission
        contactEvents.append(ContactEvent(1,13,5,True,5))  # Work transmission
        contactEvents.append(ContactEvent(1,14,5,True,5))  # Work transmission
        contactEvents.append(ContactEvent(1,5,5,False,1))  # Home non-transmission
        contactEvents.append(ContactEvent(1,6,5,False,1))  # Home non-transmission (Already infected day 3)
        # Day 6 - Index case (1) infected, infectious, symptomatic, self-isolating at home
        contactEvents.append(ContactEvent(1,5,6,False,1))  # Home non-transmission
        contactEvents.append(ContactEvent(1,6,6,False,1))  # Home non-transmission (Already infected day 3)
        # Day 7 - Index case (1) infected, infectious, symptomatic, self-isolating at home
        contactEvents.append(ContactEvent(1,5,7,True,1))   # Home transmission
        contactEvents.append(ContactEvent(1,6,7,False,1))  # Home non-transmission (Already infected day 3)
        # Day 8 - Index case (1) infected, infectious, symptomatic, self-isolating at home
        contactEvents.append(ContactEvent(1,5,8,False,1))  # Home non-transmission (Already infected day 7)
        contactEvents.append(ContactEvent(1,6,8,False,1))  # Home non-transmission (Already infected day 3)
        # Day 9 - Index case (1) infected, infectious, symptomatic, self-isolating at home
        contactEvents.append(ContactEvent(1,5,9,False,1))  # Home non-transmission (Already infected day 7)
        contactEvents.append(ContactEvent(1,6,9,False,1))  # Home non-transmission (Already infected day 3)
        # Day 10 - Index case (1) infected, recovered, at home
        contactEvents.append(ContactEvent(1,5,10,False,1))  # Home non-transmission (Already infected day 7)
        contactEvents.append(ContactEvent(1,6,10,False,1))  # Home non-transmission (Already infected day 3)
        # Day 11 - Index case (1) infected, recovered, at work
        contactEvents.append(ContactEvent(1,3,11,False,5))  # Work non-transmission
        contactEvents.append(ContactEvent(1,10,11,False,5)) # Work non-transmission
        contactEvents.append(ContactEvent(1,11,11,False,5)) # Work non-transmission
        contactEvents.append(ContactEvent(1,12,11,False,5)) # Work non-transmission
        contactEvents.append(ContactEvent(1,5,11,False,1))  # Home non-transmission (Already infected day 7)
        # Day 12 - Index case (1) infected, recovered, at work
        contactEvents.append(ContactEvent(1,2,12,False,5)) # Work non-transmission (but already infected on Day 3)
        contactEvents.append(ContactEvent(1,3,12,False,5))  # Work non-transmission
        contactEvents.append(ContactEvent(1,11,12,False,5)) # Work non-transmission
        contactEvents.append(ContactEvent(1,12,12,False,5)) # Work non-transmission
        contactEvents.append(ContactEvent(1,5,12,False,1))  # Home non-transmission (Already infected day 7)
        # Day 13->15 - No transmission data at all (should still return Rt=0 for each day)

        total_days = 15
        total_population = 10000
        summariser = InfectorSummariser(total_days,total_population)
        for ce in contactEvents:
            summariser.addRecord(ce)
            
        meanDmpPerDay = summariser.getRtCalculationAllNetworks(finalTau)

        np.testing.assert_equal(len(meanDmpPerDay),total_days,"Should be " + str(total_days) + " days worth of analysis")
        # Note that index is day-1
        assert meanDmpPerDay[0] == 0, "No transmissions"
        assert meanDmpPerDay[1] == 0, "No transmissions"
        assert meanDmpPerDay[2] > 0.00001, "Some transmissions"
        assert meanDmpPerDay[3] == 0, "No transmissions"
        assert meanDmpPerDay[4] > 0.00001, "Some transmissions"
        assert meanDmpPerDay[5] == 0, "No transmissions"
        assert meanDmpPerDay[6] > 0.00001, "Some transmissions"
        assert meanDmpPerDay[7] == 0, "No transmissions"
        assert meanDmpPerDay[8] == 0, "No transmissions"
        assert meanDmpPerDay[9] == 0, "No transmissions"
        assert meanDmpPerDay[10] == 0, "No transmissions"
        assert meanDmpPerDay[11] == 0, "No transmissions"
        assert meanDmpPerDay[12] == 0, "No transmissions"
        assert meanDmpPerDay[13] == 0, "No transmissions"
        assert meanDmpPerDay[14] == 0, "No transmissions"

        meanDmpPerDay = summariser.getRtCalculationByNetwork(finalTau)
        assert len(meanDmpPerDay) == 15, "Should be 15 days"
        assert len(meanDmpPerDay[0]) == 0, "Should be 0 networks on day 1"
        assert len(meanDmpPerDay[1]) == 0, "Should be 0 networks on day 2"
        assert len(meanDmpPerDay[2]) == 2, "Should be 2 networks on day 3"
        assert len(meanDmpPerDay[3]) == 2, "Should be 2 networks on day 4"
        assert len(meanDmpPerDay[4]) == 2, "Should be 2 networks on day 5"
        assert len(meanDmpPerDay[5]) == 1, "Should be 1 network on day 6"
        assert len(meanDmpPerDay[6]) == 1, "Should be 1 network on day 7"
        assert len(meanDmpPerDay[7]) == 1, "Should be 1 network on day 8"
        assert len(meanDmpPerDay[8]) == 1, "Should be 1 network on day 9"
        assert len(meanDmpPerDay[9]) == 1, "Should be 1 network on day 10"
        assert len(meanDmpPerDay[10]) == 2, "Should be 2 networks on day 11"
        assert len(meanDmpPerDay[11]) == 2, "Should be 2 networks on day 12"
        assert len(meanDmpPerDay[12]) == 0, "Should be 0 networks on day 13"
        assert len(meanDmpPerDay[13]) == 0, "Should be 0 networks on day 14"
        assert len(meanDmpPerDay[14]) == 0, "Should be 0 networks on day 15"

        assert "5" in meanDmpPerDay[2], "Network 5 should be in data"
        assert "1" in meanDmpPerDay[2], "Network 1 should be in data"
        assert "5" in meanDmpPerDay[3], "Network 5 should be in data"
        assert "1" in meanDmpPerDay[3], "Network 1 should be in data"
        assert "5" in meanDmpPerDay[4], "Network 5 should be in data"
        assert "1" in meanDmpPerDay[4], "Network 1 should be in data"
        assert "1" in meanDmpPerDay[5], "Network 1 should be in data"
        assert "1" in meanDmpPerDay[6], "Network 1 should be in data"
        assert "1" in meanDmpPerDay[7], "Network 1 should be in data"
        assert "1" in meanDmpPerDay[8], "Network 1 should be in data"
        assert "1" in meanDmpPerDay[9], "Network 1 should be in data"
        assert "5" in meanDmpPerDay[10], "Network 5 should be in data"
        assert "1" in meanDmpPerDay[10], "Network 1 should be in data"
        assert "5" in meanDmpPerDay[11], "Network 5 should be in data"
        assert "1" in meanDmpPerDay[11], "Network 1 should be in data"

        assert meanDmpPerDay[2]["5"] > 0.00001, "Some transmissions"
        assert meanDmpPerDay[2]["1"] > 0.00001, "Some transmissions"
        assert meanDmpPerDay[3]["5"] == 0, "No transmissions"
        assert meanDmpPerDay[3]["1"] == 0, "No transmissions"
        assert meanDmpPerDay[4]["5"] > 0.00001, "Some transmissions"
        assert meanDmpPerDay[4]["1"] == 0, "No transmissions"
        assert meanDmpPerDay[5]["1"] == 0, "No transmissions"
        assert meanDmpPerDay[6]["1"] > 0.00001, "Some transmissions"
        assert meanDmpPerDay[7]["1"] == 0, "No transmissions"
        assert meanDmpPerDay[8]["1"] == 0, "No transmissions"
        assert meanDmpPerDay[9]["1"] == 0, "No transmissions"
        assert meanDmpPerDay[10]["5"] == 0, "No transmissions"
        assert meanDmpPerDay[10]["1"] == 0, "No transmissions"
        assert meanDmpPerDay[11]["5"] == 0, "No transmissions"
        assert meanDmpPerDay[11]["1"] == 0, "No transmissions"



    # TODO Add a test to verify the proportion of infectious individuals in contact with m susceptible persons is calculated correctly

    