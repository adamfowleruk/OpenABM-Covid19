"""
Class representing a simulation analyser that wraps a Simulation object

Created: 8 Dec 2022
Author: Adam Fowler <adam@adamfowler.org> <adam.fowler@spc.ox.ac.uk>
"""

import math

# Utility classes first


# Worker classes

class SimulationAnalyser:
    sim = 0

    # TRACING VARIABLES DURING SIM
    valuesWork = []
    valuesHome = []
    valuesRandom = []

    contactEvents = []

    infectiousPerDay = []
    susceptiblesPerDay = []
    immunePerDay = []
    dailyRecovered = []
    hostsPerDay = []
    r0PerDay = []
    r0FixedPerDay = []
    rInstPerDay = []
    gPerDay = []
    gTenPerDay = []
    gFivePerDay = []
    gCont = []
    tauPerDay = []
    lastImmune = 0

    # TODO verify the below are used anymore...
    # From the Individual based Perspectives on R0 paper:-
    dmpPerDay = [] # Shared amongst both models
    sigmaMiPerDay = [] # Binomial individual model
    sigmaMptauPerDay = [] # Fixed model

    # From newer DMP implementation:-
    meanDmpPerDay = []

    # OUTPUT VARIABLES

    # The Tau value, from a Fixed R0 calculator, which settles over the course of a full simulation
    settledTau = 0


    def __init__(self, simToWrap):
        self.sim = simToWrap

    def simulateAndAnalyse(self, dayStartCallback = None):
        underlyingModel = self.sim.env.model

        n_total = underlyingModel._params_obj.get_param("n_total")

        # Run for sim.end_time days
        # For each simulation step, invoke a dayStartCallback, and analyse network outcomes

        for b in range(1,self.sim.end_time + 1):
            # First, call the setup per day function
            if None != dayStartCallback:
                dayStartCallback(underlyingModel)

            # Hold temporary network information - may have had parameters changed by the previous call
            for networkId in range(underlyingModel.c_model.n_networks):
                network = underlyingModel.get_network_by_id(networkId)
                
                if network.type() == 0:
                    self.valuesHome.append(network.transmission_multiplier_combined())
                elif network.type() == 1:
                    self.valuesWork.append(network.transmission_multiplier_combined())
                elif network.type() == 2:
                    self.valuesRandom.append(network.transmission_multiplier_combined())
                # See constant.h:155 INTERACTION_TYPE enum for other types (hospital networks)
            
            # Calculate R0 estimate - R = 1/ x* = 1 / (X / N) = N / X (equilibrium),
            # where N is total number of hosts, X is susceptible hosts
            # from Anderson & May Chapter 4 page 69 (The basic model: statics)
            xBar = 0
            nBar = 0
            immuneBar = 0
            infectious = 0
            dmp = 0
            # TODO should this be AFTER sim step???
            indivs = underlyingModel.get_individuals()
            for indivId in range(n_total):
                indivStatus = indivs.current_status[indivId]
                if indivStatus == 0:
                    # Susceptible
                    xBar += 1
                    nBar += 1
                    
                # 10=Death - not allowed for in Anderson & May, so discount
                # 21=Mortuary - again not allowed for
                # 9=Recovered (and immune by default in our sim run), so discount? (NO!)
                elif indivStatus == 9:
                    #nBar += 1
                    immuneBar += 1
                elif (indivStatus != 10) and (indivStatus != 21): # and (indivStatus != 9):
                    # Infected or infectious #(or recovering)
                    nBar += 1
        #             if (dayInfected[indivId] == -1):
        #                 dayInfected[indivId] = b
                
                # Asymptomatic, symptomatic, symptomatic_mild
                if (indivStatus == 3) or (indivStatus == 4) or (indivStatus == 5):
                    infectious += 1
            
            if b > 1:
                self.susceptiblesPerDay.append(xBar)
                self.hostsPerDay.append(nBar)
                self.immunePerDay.append(immuneBar)
                self.infectiousPerDay.append(infectious)
                if xBar != 0:
                    self.r0PerDay.append(nBar / xBar)
                else:
                    self.r0PerDay.append(0)
                    
                # Calculate NEWLY recovered per day
                if b > 2:
                    self.dailyRecovered.append(immuneBar - lastImmune)
                else:
                    self.dailyRecovered.append(immuneBar)
                
                if infectious > 0:
                    self.gPerDay.append(self.dailyRecovered[b - 2] / infectious)
                else:
                    self.gPerDay.append(0)
                    
                # Estimate G based on total recovered over total infectious cases
                if (b > 2):
                    totalR = 0
                    totalI = 0
                    for idx in range(0,b - 2):
                        totalR += self.dailyRecovered[idx]
                        totalI += self.infectiousPerDay[idx]
                    if (totalI > 0):
                        g = totalR / totalI
                        self.gCont.append(g)
                        
                        # We can calculate Tau per day now
                        r0 = 0
                        denom = xBar
                        if (xBar > 0):
                            r0 = (nBar / xBar)
                            denom = xBar - r0
                        if (denom > 0):
                            num = r0 * g
                            # Multiplying by n_total so we have it as a proportion of total population
                            tau = num / denom
                            self.tauPerDay.append(n_total * tau)
                            # We can now reestimate r0
                            if (g > 0):
                                self.r0FixedPerDay.append(xBar * (1 - math.exp(-tau / g)))
                            else:
                                self.r0FixedPerDay.append(0)
                        else:
                            self.tauPerDay.append(0)
                            self.r0FixedPerDay.append(0)
                    else:
                        self.gCont.append(0)
                        self.tauPerDay.append(0)
                        self.r0FixedPerDay.append(0)
                else:
                    self.gCont.append(0)
                    self.tauPerDay.append(0)
                    self.r0FixedPerDay.append(0)
                    
                # Estimate G based on last 10 days worth of data
                if b > 12:
                    recLastTen = 0
                    infectiousLastTen = 0
                    for idx in range(b - 12,b - 2):
                        recLastTen += self.dailyRecovered[idx]
                        infectiousLastTen += self.infectiousPerDay[idx]
                    if infectiousLastTen > 0:
                        self.gTenPerDay.append(recLastTen / infectiousLastTen)
                    else:
                        self.gTenPerDay.append(0)
                else:
                    self.gTenPerDay.append(0)
                # Estimate G based on last 5 days worth of data
                if b > 7:
                    recLast = 0
                    infectiousLast = 0
                    for idx in range(b - 7,b - 2):
                        recLast += self.dailyRecovered[idx]
                        infectiousLast += self.infectiousPerDay[idx]
                    if infectiousLast > 0:
                        self.gFivePerDay.append(recLast / infectiousLast)
                    else:
                        self.gFivePerDay.append(0)
                else:
                    self.gFivePerDay.append(0)
                    
                    
                lastImmune = immuneBar
            

            # Run sim
            self.sim.steps(1)

        # The simulation.py file saves summary calculations for each day in arrays (one item per day)
        self.rInstPerDay = self.sim.results["R_inst"][-(self.sim.end_time - 1):] # Last 199 elements

        self.finalTau = self.tauPerDay[len(self.tauPerDay)-1]
        
    def analyseContactEvents(self):
        underlyingModel = self.sim.env.model

        # 2. Now the simulation is complete, analyse transmission networks and calculate results

        # All contact events - whether infected or not - but ONLY when infector IS infectious
        self.contactEvents = underlyingModel.get_contact_events()
        
        print("WE HAVE FOUND " + str(len(self.contactEvents)) + " contact events")

        # TODO add InfectorSummariser use here


    def getContactEvents(self):
        return self.contactEvents

    def getFinalTau(self):
        return self.finalTau

    

    # Get results
    def getR0PerDay(self):
        return self.r0PerDay

    def getR0FixedPerDay(self):
        return self.r0FixedPerDay

    def getRInstPerDay(self):
        return self.rInstPerDay

    def getMeanDmpPerDay(self):
        return self.meanDmpPerDay