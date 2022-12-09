"""
Class representing a simulation analyser that wraps a Simulation object

Created: 8 Dec 2022
Author: Adam Fowler <adam@adamfowler.org> <adam.fowler@spc.ox.ac.uk>
"""

import math

# Utility classes first

class InfectorSummaryNetwork:
    susceptibles = set()
    infected = set()

    def __init__(self):
        self.susceptibles = set()
        self.infected = set()
        
    def addInfection(self,ce):
        self.susceptibles.add(ce.getContactId())
        if ce.wasInfectionCaused():
            self.infected.add(ce.getContactId())
            
    def getSusceptibleCount(self):
        return len(self.susceptibles)
    
    def getInfectedCount(self):
        return len(self.infected)
    

class InfectorSummary:
    networkSummaries = {} # networkIdStr -> InfectorSummaryNetwork

    def __init__(self):
        self.networkSummaries = {}

    def addInfection(self,ce):
        networkIdStr = str(ce.getNetworkId())
        if not networkIdStr in self.networkSummaries:
            self.networkSummaries[networkIdStr] = InfectorSummaryNetwork()
        self.networkSummaries[networkIdStr].addInfection(ce)
            
    def getAllSusceptibleCount(self):
        susCount = 0
        for networkIdStr in self.networkSummaries:
            susCount += self.networkSummaries[networkIdStr].getSusceptibleCount()
        return susCount
    
    def getAllInfectedCount(self):
        infCount = 0
        for networkIdStr in self.networkSummaries:
            infCount += self.networkSummaries[networkIdStr].getInfectedCount()
        return infCount
    
    def getSusceptibleCount(self,networkIdStr):
        if networkIdStr in self.networkSummaries:
            return self.networkSummaries[networkIdStr].getSusceptibleCount()
        else:
            return 0
    
    def getInfectedCount(self,networkIdStr):
        if networkIdStr in self.networkSummaries:
            return self.networkSummaries[networkIdStr].getInfectedCount()
        else:
            return 0
        
    def getNetworkIds(self):
        networkIds = set()
        for networkIdStr in self.networkSummaries:
            networkIds.add(networkIdStr)
        return networkIds
    
class InfectorList:
    infectors = {} # Dictionary using str(infectorId) -> InfectorSummary()

    def __init__(self):
        self.infectors = {}

    def addInfector(self,ce):
        # Check if index exists
        infId = str(ce.getInfectorId())
        # If it doesn't, create it
        if not infId in self.infectors:
            self.infectors[infId] = InfectorSummary()
        # Add infection record as required
        self.infectors[infId].addInfection(ce)
        
    def calcRtAllNetworks(self, finalTau, totalPopulation):
        # Determine infector set for each number of susceptibles
        infectorsBySusceptibleTotal = {}
        infectorCount = 0
        for infectorIdStr in self.infectors:
            # TODO check if it exists, and if not create a new set for Ids under the susceptibleCount in this dict
            susCountStr = str(self.infectors[infectorIdStr].getAllSusceptibleCount())
            if not susCountStr in infectorsBySusceptibleTotal:
                infectorsBySusceptibleTotal[susCountStr] = set()
            infectorsBySusceptibleTotal[susCountStr].add(infectorIdStr)
            if self.infectors[infectorIdStr].getAllInfectedCount() > 0:
                infectorCount += 1
        # Calculate Rt for each d(m,p) we have in infectorsBySusceptibleTotal
        rt = 0.0
        for countStr in infectorsBySusceptibleTotal:
            count = int(countStr) # This is 'm' from the paper
            if len(self.infectors) != 0: # Shouldn't be possible... but...
                infCount = len(infectorsBySusceptibleTotal[countStr])
#                 prop = infCount / len(self.infectors)
#                 prop = infCount / (len(self.infectors) * totalPopulation)
                prop = 0
                if infectorCount > 0:
                    prop = infCount / infectorCount # Number who passed on at least one infection per day over those infectors total who had contact with susceptibles on the same day
                # Now calculate associated probability
                prob = count * (1.0 - math.exp(-finalTau)) / totalPopulation # Should this be total population or just susceptibles?
                rt += prop * prob
        return rt
    
    def calcRtByNetwork(self, finalTau, totalPopulation):
        summaries = {} # networkIdStr -> {'infected': 0, 'suscep': 0}
        results = {}
        for infectorIdStr in self.infectors:
            infector = self.infectors[infectorIdStr]
            for networkIdStr in infector.getNetworkIds():
                if not networkIdStr in summaries:
                    summaries[networkIdStr] = {'infected':0, 'susceptibles':0, 'allInfectors': set(), 'successfulInfectors': set()}
                if not networkIdStr in results:
                    results[networkIdStr] = 0 # Rt initialisation for next loop
                newInfections = infector.getInfectedCount(networkIdStr)
                summaries[networkIdStr]["allInfectors"].add(infectorIdStr)
                if (newInfections > 0):
                    summaries[networkIdStr]["successfulInfectors"].add(infectorIdStr)
                summaries[networkIdStr]["infected"] += newInfections
                summaries[networkIdStr]["susceptibles"] += infector.getSusceptibleCount(networkIdStr)
        
        # Perform same as calcRtAllNetworks but do so by networkId
        for networkIdStr in summaries:
            infected = summaries[networkIdStr]["infected"]
            sus = summaries[networkIdStr]["susceptibles"]
            infectorCount = len(summaries[networkIdStr]["allInfectors"])
            infCount = len(summaries[networkIdStr]["successfulInfectors"])
            
            # Now its the same calculation as before
            prop = 0
            if infectorCount > 0:
                prop = infCount / infectorCount # Number who passed on at least one infection per day over those infectors total who had contact with susceptibles on the same day
            # Now calculate associated probability
            prob = sus * (1.0 - math.exp(-finalTau)) / totalPopulation # Should this be total population or just susceptibles?
            results[networkIdStr] += prop * prob
            
        return results
    
    def infectorCount(self):
#         return len(self.infectors)
        infectorCount = 0
        for infectorIdStr in self.infectors:
            if self.infectors[infectorIdStr].getAllInfectedCount() > 0:
                infectorCount += 1
        return infectorCount
    
    def susceptibleCount(self):
        susCount = 0
        for infectorIdStr in self.infectors:
            if self.infectors[infectorIdStr].getAllSusceptibleCount() > 0:
                susCount += 1
        return susCount
    
class InfectorSummariser:
    infectorDays = [] # An array by Day index (0 to days-1)
    population = 0
    
    def __init__(self, totalDays, totalPopulation):
        self.infectorDays = []
        self.population = totalPopulation
        for idx in range(0, totalDays):
            self.infectorDays.append(InfectorList())
            
    def addRecord(self,ce):
        infectorList = self.infectorDays[ce.getDay()-1]
        infectorList.addInfector(ce)
        
    def getRtCalculationAllNetworks(self,finalTau):
        rts = []
        dayIdx = 0
        for day in self.infectorDays:
            rts.append(day.calcRtAllNetworks(finalTau,self.population))
            dayIdx += 1
        return rts
    
    def getRtCalculationByNetwork(self,finalTau):
        rts = []
        for day in self.infectorDays:
            rts.append(day.calcRtByNetwork(finalTau,self.population))
        return rts
    
    def countOnDay(self,day):
        return self.infectorDays[day-1].infectorCount()
    
    def susOnDay(self,day):
        return self.infectorDays[day-1].susceptibleCount()
        

# Worker classes

class SimulationAnalyser:
    sim = 0

    # TRACING VARIABLES DURING SIM
    valuesWork = []
    valuesHome = []
    valuesRandom = []

    contactEvents = []
    summariser = 0

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
    networkMeanDmpPerDaySource = []

    # OUTPUT VARIABLES

    # The Tau value, from a Fixed R0 calculator, which settles over the course of a full simulation
    settledTau = 0


    def __init__(self, simToWrap):
        self.sim = simToWrap

        self.valuesWork = []
        self.valuesHome = []
        self.valuesRandom = []

        self.contactEvents = []
        self.summariser = 0

        self.infectiousPerDay = []
        self.susceptiblesPerDay = []
        self.immunePerDay = []
        self.dailyRecovered = []
        self.hostsPerDay = []
        self.r0PerDay = []
        self.r0FixedPerDay = []
        self.rInstPerDay = []
        self.gPerDay = []
        self.gTenPerDay = []
        self.gFivePerDay = []
        self.gCont = []
        self.tauPerDay = []
        self.lastImmune = 0

        self.dmpPerDay = [] # Shared amongst both models
        self.sigmaMiPerDay = [] # Binomial individual model
        self.sigmaMptauPerDay = [] # Fixed model

        self.meanDmpPerDay = []
        self.networkMeanDmpPerDaySource = []

        self.settledTau = 0

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

        n_total = underlyingModel._params_obj.get_param("n_total")
        self.summariser = InfectorSummariser(self.sim.end_time, n_total)
        for ce in self.contactEvents:
            self.summariser.addRecord(ce)
            
        self.meanDmpPerDay = self.summariser.getRtCalculationAllNetworks(self.finalTau)

        # print("Infector count on day 10: " + str(self.summariser.countOnDay(10)) + " and sus: " + str(self.summariser.susOnDay(10)))
        # print("Infector count on day 30: " + str(self.summariser.countOnDay(30)) + " and sus: " + str(self.summariser.susOnDay(30)))
        # print("Infector count on day 50: " + str(self.summariser.countOnDay(50)) + " and sus: " + str(self.summariser.susOnDay(50)))
        # print("Infector count on day 100: " + str(self.summariser.countOnDay(100)) + " and sus: " + str(self.summariser.susOnDay(100)))

        # def printCE(ce):
        #     print("Day: " + str(ce.getDay()) + " networkId: " + str(ce.getNetworkId()) + " infectorId: " + str(ce.getInfectorId()) + 
        #         " contactId: " + str(ce.getContactId()) + " wasInfected?: " + str(ce.wasInfectionCaused()))

        # printCE(self.contactEvents[0])
        # printCE(self.contactEvents[50])
        # printCE(self.contactEvents[500])
        # printCE(self.contactEvents[1000])
        # printCE(self.contactEvents[2000])
        # printCE(self.contactEvents[3000])
        # printCE(self.contactEvents[4000])
        # printCE(self.contactEvents[5000])
        # printCE(self.contactEvents[20000])
        # printCE(self.contactEvents[50000])

        # currently day,network
        self.networkMeanDmpPerDaySource = self.summariser.getRtCalculationByNetwork(self.finalTau)

        self.networkDayDmp = {} # networkIdStr -> [day] -> Rt

        dayIndex = 0
        for dayData in self.networkMeanDmpPerDaySource:
            dayIndex += 1
            for networkIdStr in dayData:
                if not networkIdStr in self.networkDayDmp:
                    self.networkDayDmp[networkIdStr] = []
                self.networkDayDmp[networkIdStr].append(dayData[networkIdStr])


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

    def getDmpByNetwork(self):
        return self.networkDayDmp