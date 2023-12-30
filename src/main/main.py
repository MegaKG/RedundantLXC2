#!/usr/bin/env python3
import Registry_handler
import LXC_handler
import Node_handler
import DataObjects

import time
import operator

class main:
    def __init__(self,config):
        self.config = config

        #Initialise the Wrapper Objects
        self.database = Registry_handler.MasterRegistry(
            config['Database']['Host'],
            config['Database']['Username'],
            config['Database']['Password'],
            config['Database']['Port'],
            config['Database']['Database']
        )
        self.database.generateTables()
        print("INFO:","Init Database Connection")

        self.node = Node_handler.node()
        print("INFO:","Init Node Utils")

        self.lxc = LXC_handler.lxcHandler()
        print("INFO:","Init LXC Connector")

        #Clean the Database
        self.database.clean(self.config['Poller']['MissedInterval'])
        print("INFO:","Cleaned DB")

        #self.database.setDebug()

        self.MyNode = DataObjects.Node(-1,"Unknown",0,"Unknown")
        self.MyZones = []
        self.refreshNodeInfo()

        #Container Lists
        self.ToStart = [] # Contains those to start
        self.ToStop = [] # Contains those to stop
        self.PausedContainers = {} # Contains those that must have no action within the timeframe

        #print("Startup State")
        #self.database.dumpTableStates()

    def refreshNodeInfo(self):
        #Get My Node ID First
        MyNodeID = self.database.getNodeIDByName(self.node.getHostname())

        if MyNodeID < 0:
            print("ERROR: Node not in Database, Cannot Refresh")
            return

        #Get the Node Object
        self.MyNode = self.database.queryNodeInfo(MyNodeID)
        #print("Got My Node Info")

        #Update the last seen time
        self.database.updateNodeTime(MyNodeID)

        #Get the Zones for the node
        self.MyZones = self.database.getZoneIDsForNode(self.MyNode.ID)


    def genColdStartList(self):
        #Get Currently Running Containers
        LocalRunning = self.lxc.listRunningContainers()

        #For Each Zone I am in
        for ZoneID in self.MyZones:
            #Get the Missing Containers in Each Zone
            MissingContainers = self.database.getMissingContainerIDsforZone(ZoneID,self.MyNode.Arch)
            #print("Missing",MissingContainers)

            #For each Container ID, query the container and add it to a dictionary
            #Matching priorities are in a list
            Priorities = {}
            for ContainerID in MissingContainers:
                ContainerObject = self.database.queryContainerInfo(ContainerID)
                if ContainerObject.Priority not in Priorities:
                    Priorities[ContainerObject.Priority] = [ContainerObject]
                else:
                    Priorities[ContainerObject.Priority].append(ContainerObject)
            #print("Pri",Priorities)

            #Determine Budget and Current Usage
            Results = self.database.getUsageAndBudgetForNode(self.MyNode.ID)
            if Results == False:
                Usage = 0
                Budget = self.MyNode.Budget
            else:
                Budget = Results['Budget']
                Usage = Results['Usage']

            #Determine containers to start
            for Priority in sorted(Priorities.keys(),reverse=True):
                #print(Priority,Priorities[Priority])
                for Container in Priorities[Priority]:
                    if ((Usage + Container.Cost) <= Budget) and (Container.Name not in LocalRunning):
                        print("Start",Container)
                        self.ToStart.append(Container.ID)
                        Usage += Container.Cost
    
    def genUnassignedStopList(self):
        #print("Pre Unassigned")
        #self.database.dumpTableStates()
        
        #Get Running Containers
        LocalRunningNames = self.lxc.listRunningContainers()

        #Get Assigned Containers
        NotAssignedIDs = self.database.getContainersNotAssignedToNode(self.MyNode.ID)
        #print("Not Assigned",NotAssignedIDs)


        #Iterate over the local ones
        #print("Check Unassigned",LocalRunningNames,NotAssignedIDs)
        for LocalContainerName in LocalRunningNames:
            LocalContainerID = self.database.getContainerIDByName(LocalContainerName)

            if (LocalContainerID in NotAssignedIDs):
                print("Container not Assigned",LocalContainerID)
                self.ToStop.append(LocalContainerID)

    def deleteNotRunning(self):
        #Delete not running containers from the record
        ActuallyRunningNames = self.lxc.listRunningContainers()

        ActuallyRunningIDs = []
        for Name in ActuallyRunningNames:
            ID = self.database.getContainerIDByName(Name)
            
            #IDs below Zero indicate missing information and are skipped
            if ID >= 0:
                ActuallyRunningIDs.append(ID)

        #Get the Apparent Running
        ApparentRunningIDs = self.database.getContainersAssignedToNode(self.MyNode.ID)

        for ContainerID in ApparentRunningIDs:
            if ContainerID not in ActuallyRunningIDs:
                C = self.database.queryContainerInfo(ContainerID)
                print("INFO: Container",ContainerID,C.Name,"Is not actually running")
                
                #Cull It from the Database
                self.database.removeRunningContainer(ContainerID,self.MyNode.ID)


    def reallocateBalanceContainers(self):
        #Get my Current Usage
        Results = self.database.getUsageAndBudgetForNode(self.MyNode.ID)
        if not Results:
            print("No Usage Reported")
            return
        
        Budget = Results['Budget']
        Usage = Results['Usage']

        #For each zone, check the global usage
        for ZoneID in self.MyZones:
            #Query the Zone Usage by Node
            ZoneUsages = self.database.getZoneUsageByName(ZoneID)
            #print("USAGE",ZoneUsages)
            #print("Usage")
            #print("ID:\tBG:\t\tUS:\t\tPC:")
            #for NodeID in ZoneUsages:
            #    print(NodeID,'\t',ZoneUsages[NodeID]['Budget'],'\t\t',ZoneUsages[NodeID]['Usage'],'\t\t',100*(ZoneUsages[NodeID]['Usage']/ZoneUsages[NodeID]['Budget']))

            if len(ZoneUsages) > 0:
                #Find the Node with the Lowest Usage
                MinimumKey = list(ZoneUsages.keys())[0]
                MinimumValue = ZoneUsages[MinimumKey]['Usage']

                for NodeID in ZoneUsages:
                    if ZoneUsages[NodeID]['Usage'] < MinimumValue:
                        MinimumKey = NodeID
                        MinimumValue = ZoneUsages[NodeID]['Usage']
                
                #Make sure that it isn't us
                if MinimumKey != self.MyNode.ID:
                    #Get My Containers
                    MyContainerIDs = self.database.getContainersAssignedToNode(self.MyNode.ID)

                    for ContainerID in MyContainerIDs:
                        #Get the Container Information
                        ContainerObject = self.database.queryContainerInfo(ContainerID)

                        #Check if it fits
                        if ((Usage - ContainerObject.Cost)/Budget) > ((MinimumValue + ContainerObject.Cost)/ZoneUsages[MinimumKey]['Budget']):
                            print("INFO:Transfer",ContainerID, "Cost",ContainerObject.Cost,"From",self.MyNode.ID,"To",MinimumKey)
                            print("From ",(Usage - ContainerObject.Cost)/Budget, " to ",(MinimumValue + ContainerObject.Cost)/ZoneUsages[MinimumKey]['Budget'])
                            #Move it
                            self.lxc.awaitStop(ContainerObject.Name)
                            
                            #Transfer Ownership
                            self.database.removeRunningContainer(ContainerID,self.MyNode.ID)
                            self.database.addRunningContainer(ContainerID,MinimumKey)

                            #Update the Costs
                            Usage -= ContainerObject.Cost
                            MinimumValue += ContainerObject.Cost

                    


            
    def startContainers(self):
        for ContainerID in self.ToStart:
            if ContainerID not in self.PausedContainers:
                #print("INFO:","Starting Container with ID",ContainerID)
                Container = self.database.queryContainerInfo(ContainerID)
                #print("Found Container",ContainerID,"Has Name",Container.Name)

                Result = self.lxc.awaitStart(Container.Name)
                if Result:
                    print("INFO:","Successfully Started",ContainerID,"(",Container.Name,")")
                    
                    #Add it to the database
                    self.database.addRunningContainer(ContainerID,self.MyNode.ID)
                else:
                    print("WARN:","Failed to Start",ContainerID,"(",Container.Name,") Timed Out")
                    self.database.flagContainer(self.MyNode.ID,ContainerID)

                #Mark it
                self.PausedContainers[ContainerID] = time.time()


    def stopContainers(self):
        for ContainerID in self.ToStop:
            if ContainerID not in self.PausedContainers:
                #print("INFO:","Stopping Container with ID",ContainerID)
                Container = self.database.queryContainerInfo(ContainerID)
                #print("Found Container",ContainerID,"Has Name",Container.Name)

                Result = self.lxc.awaitStop(Container.Name)
                if Result:
                    print("INFO:","Successfully Stopped",ContainerID,"(",Container.Name,")")

                    self.database.removeRunningContainer(ContainerID,self.MyNode.ID)
                else:
                    print("WARN:","Failed to Stop",ContainerID,"(",Container.Name,") Timed Out")
                    self.database.flagContainer(self.MyNode.ID,ContainerID)

                #Mark it
                self.PausedContainers[ContainerID] = time.time()


    def markAllCurrentlyRunningContainers(self):
        #Get the Containers currently Running
        Running = self.lxc.listRunningContainers()

        #Generate a list for all containers running in my zones
        AllRunning = []
        for ZoneID in self.MyZones:
            ZoneRunningContainerIDs = self.database.getZoneContainersRunning(ZoneID)
            AllRunning += ZoneRunningContainerIDs

        #For each container currently running
        for ContainerName in Running:
            #Get ID from the Database
            CID = self.database.getContainerIDByName(ContainerName)
            if CID < 0:
                print("WARN:",ContainerName,"Not in DB")
            else:
                #If it is not marked as up, mark it
                if CID not in AllRunning:
                    print("WARN:",ContainerName,"Not Marked, marking...")
                    self.database.addRunningContainer(CID,self.MyNode.ID)


    def clearLists(self):
        self.ToStart = []
        self.ToStop = []  

        for ID in list(self.PausedContainers.keys()):
            if (time.time() - self.PausedContainers[ID]) > self.config['Poller']['MissedInterval']:
                del self.PausedContainers[ID] 

    def run(self):
        self.refreshNodeInfo()

        #Prefill the database
        self.markAllCurrentlyRunningContainers()
                

        #Main Loop
        last = time.time()
        while True:
            now = time.time()
            #Wait until poll time
            if (now - last) > self.config['Poller']['CheckInterval']:
                #print("Cycle")
                #Clear the arrays of actions
                self.clearLists()
 
                #Get My node Information
                self.refreshNodeInfo()

                #Mark any Containers that were missed
                self.markAllCurrentlyRunningContainers()

                #Clean the Database
                self.database.clean(self.config['Poller']['MissedInterval'])
                self.deleteNotRunning()

                #Check what needs to be done with the containers
                self.genUnassignedStopList()
                self.reallocateBalanceContainers()
                self.genColdStartList()


                #Ensure that there are no conflicts
                for ID in self.ToStop:
                    if ID in self.ToStart:
                        self.ToStart.remove(ID)

                self.startContainers()
                self.stopContainers()


                last = time.time()

            else:
                time.sleep(1)


if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) == 1:
        configFile = '/etc/FailConfig.json'
    else:
        configFile = sys.argv[1]
    print("INFO: Loading config from",configFile)

    f = open(configFile,'r')
    config = json.loads(f.read())
    f.close()

    service = main(config)
    service.run()