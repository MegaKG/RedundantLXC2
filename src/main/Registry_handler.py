import Database_handler
import time
import DataObjects
import Queries

class MasterRegistry(Database_handler.database):
    #Debug Stuff, dumps the tables nicely
    def dumpTableStates(self):
        Tables = self._colselect(self._runquery("show tables;"),0)
        spacer = ' | '
        def _pad(Data,Length):
            out = str(Data)
            while len(out) < Length:
                out += ' '
            return out
        
        for table in Tables:
            Headers = self._colselect(self._runquery("describe `{}`;".format(table)),0)

            ColumnLengths = []
            for header in Headers:
                ColumnLengths.append(len(header))

            Data = self._runquery("select * from `{}`;".format(table))
            for row in Data:
                for columnID, columnData in enumerate(row):
                    if len(str(columnData)) > ColumnLengths[columnID]:
                        ColumnLengths[columnID] = len(str(columnData))


            TotalWidth = sum(ColumnLengths) + (len(ColumnLengths) * len(spacer))
            print("\n[ {} ]".format(table))
            print('=' * (TotalWidth + 1))

            strRow = ''
            for index in range(len(ColumnLengths)):
                strRow += _pad(Headers[index],ColumnLengths[index]) + spacer

            print('| ' + strRow)
            print('=' * (TotalWidth + 1))

            for row in Data:
                strRow = ''
                for index in range(len(ColumnLengths)):
                    strRow += _pad(row[index],ColumnLengths[index]) + spacer
                print('| ' + strRow)

            print('=' * (TotalWidth + 1) + '\n')

            


    #Queries Start Here
    #Administrative Stuff
    def generateTables(self):
        #Create the Schema if the don't exist already
        for statement in Queries.CreateStatements:
            self._runquery(statement)

    def clean(self,Interval):
        #Get the Current Time
        current = int(time.time())

        #Run the Query
        self._runquery(Queries.CleanNodes,current,Interval)
        self._runquery(Queries.CleanStatus)

    
    #Query Data Objects
    #Container Information
    def queryContainerInfo(self,ID):
        #Query Info
        Results = self._runquery(Queries.ContainerInfo,ID)
        if len(Results) == 0:
            return None
        else:
            return DataObjects.Container(ID,Results[0][0],Results[0][1],Results[0][2],Results[0][3],Results[0][4])
    
    #Node Information
    def queryNodeInfo(self,ID):
        #Query Info
        Results = self._runquery(Queries.NodeInfo,ID)
        if len(Results) == 0:
            return None
        else:
            return DataObjects.Node(ID,Results[0][0],Results[0][1],Results[0][2])

        
    #Zone Information
    def queryZoneInfo(self,ID):
        #Query Info
        Results = self._runquery(Queries.ZoneInfo,ID)
        if len(Results) == 0:
            return None
        else:
            return DataObjects.Zone(ID,Results[0][0],self.queryZoneMembers(ID))
            
        
    #Zone Members
    def queryZoneMembers(self,ID):
        #Query Info
        Results = self._runquery(Queries.ZoneMembers,ID)

        #Select the Column
        Nodes = self._colselect(Results,0)

        if self.debug:
            print("The Zone",ID,"Has the Following Nodes")
            for i in Nodes:
                N = self.queryNodeInfo(i)
                print("-->",N.ID,N.Name,N.Budget,N.Arch)

        return Nodes


    #Zones for Node  
    def getZoneIDsForNode(self,ID):
        #Query Info
        Results = self._runquery(Queries.ZonesForNode,ID)

        #Select the Column
        Zones = self._colselect(Results,0)

        if self.debug:
            print("The Node",ID,"Has the Following Zones")
            for i in Zones:
                Z = self.queryZoneInfo(i)
                print("-->",Z.ID,Z.Name,Z.Nodes)

        return Zones
        
    #Active members in a Zone
    def queryRunningZoneMembers(self,ID):
        #Query Info
        Results = self._runquery(Queries.ZoneRunningMembers,ID)

        #Select the Column
        Nodes = self._colselect(self.cursor.fetchall(),0)

        if self.debug:
            print("The Zone",ID,"Has the Following Running Nodes")
            for i in Nodes:
                N = self.queryNodeInfo(i)
                print("-->",N.ID,N.Name,N.Budget,N.Arch)

        return Nodes

    
    #Name to ID Conversions
    #Container 
    def getContainerIDByName(self,Name):
        #Query Info
        Results = self._runquery(Queries.ContainerIDByName,Name)
        
        if len(Results) == 0:
            return -1
        else:
            return Results[0][0]
        
        
    #Node
    def getNodeIDByName(self,Name):
        #Query Info
        Results = self._runquery(Queries.NodeIDByName,Name)
        
        if len(Results) == 0:
            return -1
        else:
            return Results[0][0]
        
    #Zone
    def getZoneIDByName(self,Name):
        #Query Info
        Results = self._runquery(Queries.ZoneIDByName,Name)
        
        if len(Results) == 0:
            return -1
        else:
            return Results[0][0]
        

    #Set Container Status
    #Remove from Running List
    def removeRunningContainer(self,CID,NID):
        #print("***DELETE",CID,NID)
        #Execute
        self._runquery(Queries.RemoveRunning,CID,NID)
        self.dbprint("Remove Running",CID,"on Node",NID)

    #Add to Running List
    def addRunningContainer(self,CID,NID):
        #Execute
        self._runquery(Queries.AddRunning,CID,NID)
        self.dbprint("Add Running",CID,"on Node",NID)


    #Update the Timestamp for last seen
    def updateNodeTime(self,NID):
        #Execute
        self._runquery(Queries.UpdateNode,NID,int(time.time()))
        self.dbprint("Update Timestamp")

    #Flag a container to prevent from launch
    def flagContainer(self,NID,CID):
        flagTime = time.time()

        #Execute
        self._runquery(Queries.FlagContainer,CID,NID,flagTime)
        self.dbprint("Flagged Container",CID,"On Node",NID)

        
    #General Queries
    def getMissingContainerIDsforZone(self,ZoneID, Architecture):
        #Query Info
        Results = self._runquery(Queries.FindMissingContainersForZone,ZoneID,Architecture)
        return self._colselect(Results,0)
    
    #Get the usage and budget for a node 
    def getUsageAndBudgetForNode(self,ID):
        #Query Info
        #print(Queries.UsageAndBudgetForNode,ID)
        Results = self._runquery(Queries.UsageAndBudgetForNode,ID)
        if len(Results) > 0:
            return {"Usage":Results[0][0],"Budget":Results[0][1]}
        else:
            return False
        
    #Get Containers assigned to Node
    def getContainersAssignedToNode(self,ID):
        #Query Info
        Results = self._runquery(Queries.ContainersAssignedToNode,ID)
        return self._colselect(Results,0)
    
    #Get Containers available to Node
    def getContainersAvailableToNode(self,ID):
        #Query Info
        Results = self._runquery(Queries.ContainersAvailableToNode,ID)
        return self._colselect(Results,0)
    
    #Get Usage for Zone
    def getZoneUsageByName(self,ID):
        #Query Info
        Results = self._runquery(Queries.ZoneUsage,ID)
        
        Out = {}
        for index in range(len(Results)):
            Out[Results[index][0]] = {'Budget':Results[index][1],'Usage':Results[index][2]}
        
        return Out
    
    #Get Containers running in zone
    def getZoneContainersRunning(self,ID):
        #Query Info
        Results = self._runquery(Queries.ZoneContainersRunning,ID)
        return self._colselect(Results,0)
    
    #Get Containers assigned to Node
    def getContainersNotAssignedToNode(self,ID):
        #Query Info
        Results = self._runquery(Queries.ContainersNotAssignedToNode,ID)
        return self._colselect(Results,0)
  
    