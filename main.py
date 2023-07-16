#!/usr/bin/env python3
import Database_handler
import LXC_handler
import Node_handler

import time
import operator

class main:
    def __init__(self,config):
        self.config = config

        #Initialise the Wrapper Objects
        self.database = Database_handler.database(
            config['Database']['Host'],
            config['Database']['Username'],
            config['Database']['Password'],
            config['Database']['Port'],
            config['Database']['Database']
        )
        print("INFO:","Init Database Connection")

        self.node = Node_handler.node()
        print("INFO:","Init Node Utils")

        self.lxc = LXC_handler.lxcHandler()
        print("INFO:","Init LXC Connector")

        #Clean the Database
        self.database.clean(self.config['Poller']['MissedInterval'])
        print("INFO:","Cleaned DB")

        #self.database.setDebug()

        self.MyNode = None
        self.refreshNodeInfo()

        #Container Lists
        self.ToStart = [] # Contains those to start
        self.ToStop = [] # Contains those to stop
        self.PausedContainers = {} # Contains those that must have no action within the timeframe

    def refreshNodeInfo(self):
        #Get My Node ID First
        MyNodeID = self.database.getNodeIDByName(self.node.getHostname())

        if MyNodeID < 0:
            print("ERROR: Node not in Database, Cannot Refresh")
            return

        #Get the Node Object
        self.MyNode = self.database.queryNodeInfo(MyNodeID)
        #print("Got My Node Info")

        self.database.updateNodeTime(MyNodeID)


    def genColdStartList(self):
        #Determine the Current Resource Usage
        CurrentUsage = self.database.getNodeCostUsage(self.MyNode.ID)
        #print("Current Usage",CurrentUsage)
        
        #Get a List of Missing Containers assigned to me
        Missing = self.database.getMissingContainersFor(self.MyNode.ID)

        #Get their Information
        MissingContainers = []
        for ID in Missing:
            MissingContainers.append(self.database.queryContainerInfo(ID))
            print("INFO: Missing Container",ID,MissingContainers[-1].Name)


        #Sort by Priority, Largest First
        SortedMissingContainers = sorted(MissingContainers, key=operator.attrgetter('Priority'), reverse=True)

        #Determine how many can be started within our budget
        AccumCost = CurrentUsage
        for Container in SortedMissingContainers:
            #First Check if We are the Node with the lowest used percentage in the cluster
            HighestPercentage = 0

            #Query the Zone
            ZoneUsage = self.database.getZoneUsageByNode(Container.Zone,self.config['Poller']['MissedInterval'])
            for NodeID in ZoneUsage:
                if ZoneUsage[NodeID] > HighestPercentage:
                    #print("Highest Node",NodeID)
                    HighestPercentage = ZoneUsage[NodeID]

            #Calculate My Usage
            MyUsage = AccumCost / self.MyNode.Budget
            #print("My Usage",MyUsage)

            if (AccumCost + Container.Cost) < self.MyNode.Budget:
                if HighestPercentage >= MyUsage:
                    if self.MyNode.Arch == Container.Arch:
                        if (self.node.getMemoryUsage() < self.config['Limits']['RAM']) and (self.node.getProcessorUsage() < self.config['Limits']['CPU']):
                            self.ToStart.append(Container.ID)
                            AccumCost += Container.Cost
                        else:
                            print("WARN: Skip",Container.Name,"Reason: Not Enough System Resources")
                    else:
                        print("WARN: Skip",Container.Name,"Reason: Incompatible Arch")
                else:
                    print("WARN: Skip",Container.Name,"Reason: For Other Nodes")
            else:
                print("WARN: Skip",Container.Name,"Reason: Out of Budget")

            
    def genUnassignedStopList(self):
        #Get a list of nodes assigned to me
        Assigned = self.database.getContainersFor(self.MyNode.ID)
        #print("I am assigned",Assigned)

        #Get a list of running containers on the cluster
        RegisteredRunning = self.database.getRunningContainersFor(self.MyNode.ID)

        #Get Running
        Running = self.lxc.listRunningContainers()

        #Check what we shouldn't have
        for ContainerName in Running:
            ID = self.database.getContainerIDByName(ContainerName)

            if ID < 0:
                #print("Ignore Running",ID,"(",ContainerName,")")
                pass
            else:
                if (ID not in Assigned) or (ID not in RegisteredRunning):
                    print("INFO: Container",ID,"(",ContainerName,") Should not Be Running")
                    self.ToStop.append(ID)


        
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
        ApparentRunningIDs = self.database.getRunningContainersFor(self.database.getNodeIDByName(self.node.getHostname()))

        for ContainerID in ApparentRunningIDs:
            if ContainerID not in ActuallyRunningIDs:
                C = self.database.queryContainerInfo(ContainerID)
                print("INFO: Container",ContainerID,C.Name,"Is not actually running")
                
                #Cull It
                self.database.removeRunningContainer(ContainerID,self.MyNode.ID)


    def reallocateBalanceContainers(self):

        #Get the Container I have running
        MyRunning = self.database.getRunningContainersFor(self.MyNode.ID)
        MyLoad = self.database.getNodeCostUsage(self.MyNode.ID)

        for ContainerID in MyRunning:
            #Get the Container Info
            Container = self.database.queryContainerInfo(ContainerID)
            
            #Get the Node Scores in the Zone
            ZoneScores = self.database.getZoneUsageByNode(Container.ID,self.config['Poller']['MissedInterval'])
            #print("Scores",ZoneScores)

            #Find the Node with the Minimum Usage
            Keys = list(ZoneScores.keys())
            if len(Keys) > 0:
                MinID = Keys[0]
                Min = ZoneScores[MinID]

                for key in Keys:
                    if ZoneScores[key] < Min:
                        Min = ZoneScores[key]
                        MinID = key

                #print("Selected Minimum Node",MinID,"Name",self.database.queryNodeInfo(MinID))

                #Now we query that node if it isn't us
                if MinID != self.MyNode.ID:
                    #We will drop the container if they can handle it
                    TheirNode = self.database.queryNodeInfo(MinID)

                    #Calculate the Total Container Load
                    TheirTotalLoad = self.database.getNodeCostUsage(TheirNode.ID)
                    #print("Their Raw Load is ",TheirTotalLoad,"of",TheirNode.Budget)
                    #print("My Raw Load is ",MyLoad,"of",self.MyNode.Budget)

                    #print("I am looking to move",ContainerID,"(",Container.Name,") to node ",MinID,"(",TheirNode.Name,") of cost ",Container.Cost)

                    MyNewLoad = float((MyLoad - Container.Cost)/self.MyNode.Budget)
                    TheirNewLoad = float((TheirTotalLoad + Container.Cost)/TheirNode.Budget)

                    #print(MyNewLoad,TheirNewLoad)
                    

                    if (abs(MyNewLoad - TheirNewLoad) <= 0.0001) or (MyNewLoad > TheirNewLoad):
                        print("INFO:","Moving Container",Container.Name,"with cost",Container.Cost,"to Node",TheirNode.Name)

                        self.ToStop.append(ContainerID)


            


    def startContainers(self):
        for ContainerID in self.ToStart:
            if ContainerID not in self.PausedContainers:
                print("INFO:","Starting Container with ID",ContainerID)
                Container = self.database.queryContainerInfo(ContainerID)
                #print("Found Container",ContainerID,"Has Name",Container.Name)

                Result = self.lxc.awaitStart(Container.Name)
                if Result:
                    print("INFO:","Successfully Started",ContainerID,"(",Container.Name,")")
                    
                    #Add it to the database
                    self.database.addRunningContainer(ContainerID,self.MyNode.ID)
                else:
                    print("WARN:","Failed to Start",ContainerID,"(",Container.Name,") Timed Out")

                #Mark it
                self.PausedContainers[ContainerID] = time.time()


    def stopContainers(self):
        for ContainerID in self.ToStop:
            if ContainerID not in self.PausedContainers:
                print("INFO:","Stopping Container with ID",ContainerID)
                Container = self.database.queryContainerInfo(ContainerID)
                #print("Found Container",ContainerID,"Has Name",Container.Name)

                Result = self.lxc.awaitStop(Container.Name)
                if Result:
                    print("INFO:","Successfully Stopped",ContainerID,"(",Container.Name,")")

                    self.database.removeRunningContainer(ContainerID,self.MyNode.ID)
                else:
                    print("WARN:","Failed to Stop",ContainerID,"(",Container.Name,") Timed Out")

                #Mark it
                self.PausedContainers[ContainerID] = time.time()

    def clearLists(self):
        self.ToStart = []
        self.ToStop = []  

        for ID in list(self.PausedContainers.keys()):
            if (time.time() - self.PausedContainers[ID]) > self.config['Poller']['MissedInterval']:
                del self.PausedContainers[ID] 

    def run(self):
        self.refreshNodeInfo()

        last = time.time()


        #Prefill the database
        Running = self.lxc.listRunningContainers()
        AllRunning = self.database.getRunningContainers()

        for ContainerName in Running:
            CID = self.database.getContainerIDByName(ContainerName)
            if CID < 0:
                print("WARN:",ContainerName,"Not in DB")
            else:
                #Get if running
                if CID not in AllRunning:
                    print("WARN:",ContainerName,"Not Marked, marking...")
                    self.database.addRunningContainer(CID,self.MyNode.ID)
                

        #Main Loop
        while True:
            now = time.time()
            #Wait until poll time
            if (now - last) > self.config['Poller']['CheckInterval']:
                #Clear the arrays of actions
                self.clearLists()

                #Get My node Information
                self.refreshNodeInfo()

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

    configFile = sys.argv[1]
    print("INFO: Loading config from",configFile)

    f = open(configFile,'r')
    config = json.loads(f.read())
    f.close()

    service = main(config)
    service.run()