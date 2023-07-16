import mysql.connector as mc
import time
import DataObjects

class database:
    def _tableExists(self,TableName):
        self.cursor.execute('show tables;')
        Out = []
        for i in self.cursor.fetchall():
            Out.append(i[0])
        
        return TableName in Out

    def _connect(self):
        self.db = mc.connect(
                host = self._Host,
                user = self._Username,
                passwd = self._Password,
                database = self._DB,
                port = self._Port
            )
        self.cursor = self.db.cursor()

        #Create the Schema if the don't exist already
        CreateStatements = [
            "create table if not exists Nodes(`NID` INT NOT NULL, `Name` VARCHAR(64) NOT NULL, `Budget` INT NOT NULL, `Arch` VARCHAR(16), `LastSeen` BIGINT(255) NOT NULL, PRIMARY KEY(`NID`));",
            "create table if not exists Zones(`ZID` INT NOT NULL, `Name` VARCHAR(64) NOT NULL, PRIMARY KEY(`ZID`));",
            "create table if not exists Containers(`CID` INT NOT NULL, `Name` VARCHAR(64) NOT NULL, `Priority` INT NOT NULL, `Cost` INT NOT NULL, `Zone` INT NOT NULL, `Arch` VARCHAR(16), PRIMARY KEY(`CID`), FOREIGN KEY(`Zone`) REFERENCES Zones(`ZID`));",
            "create table if not exists ZoneMembership(`ZID` INT NOT NULL, `NID` INT NOT NULL, PRIMARY KEY(`ZID`,`NID`), FOREIGN KEY(`ZID`) REFERENCES Zones(`ZID`), FOREIGN KEY(`NID`) REFERENCES Nodes(`NID`));",
            "create table if not exists ContainerStatus(`NID` INT NOT NULL, `CID` INT NOT NULL, PRIMARY KEY(`CID`), FOREIGN KEY(`NID`) REFERENCES Nodes(`NID`), FOREIGN KEY(`CID`) REFERENCES Containers(`CID`));"
        ]

        for statement in CreateStatements:
            self.cursor.execute(statement)
            self.cursor.fetchall()
        print("Connected to DB")

    def _recover(self):
        print("ERROR","Something Broke in the Database, attempting recovery")
        self.Status = False
        while True:
            try:
                self._connect()
                self.Status = True
                break
            except Exception as E:
                print("DB Connect Error",E)
                time.sleep(1)


    def __init__(self,Host,Username,Password,Port,DB):
        self._Host = Host
        self._Username = Username
        self._Password = Password
        self._Port = Port
        self._DB = DB
        self._recover()

        self.debug = False

    def setDebug(self):
        self.debug = True

    def dbprint(self,*n):
        if self.debug:
            print(*n)

    def _colselect(self,Data,index):
        out = []
        for i in Data:
            out.append(i[index])
        return out

    def clean(self,Interval):
        try:
            current = time.time()

            #Get the Current Stale Nodes
            self.cursor.execute("select NID from Nodes where (%s - LastSeen) > %s;",(current,Interval))
            StaleNodes = self._colselect(self.cursor.fetchall(),0)

            #Delete the Stale Nodes
            for nodeID in StaleNodes:
                self.dbprint("Stale Node",nodeID,self.queryNodeInfo(nodeID).Name)
                self.cursor.execute("delete from ContainerStatus where NID = %s;",(nodeID,))

        except Exception as E:
            self.setDebug()
            self._recover()
            self.clean(Interval)

    def getRunningContainers(self):
        try:
            self.cursor.execute("select C.CID as Node from (Containers C natural join ContainerStatus S) join Nodes N on S.NID = N.NID;")
            RunningContainers = self._colselect(self.cursor.fetchall(),0)

            if self.debug:
                print("The Following Containers are Running:")
                for i in RunningContainers:
                    C = self.queryContainerInfo(i)
                    print("-->",i,C.Name,C.Cost,C.Priority,C.Zone,C.Arch)

            return RunningContainers
        
        except Exception as E:
            self.setDebug()
            self._recover()
            return self.getRunningContainers()
    
    def getRunningContainersFor(self,ID):
        try:
            self.cursor.execute("select C.CID as Node from (Containers C natural join ContainerStatus S) join Nodes N on S.NID = N.NID where N.NID = %s;",(ID,))
            RunningContainers = self._colselect(self.cursor.fetchall(),0)

            if self.debug:
                print("The Following Containers are Running on host:")
                for i in RunningContainers:
                    C = self.queryContainerInfo(i)
                    print("-->",i,C.Name,C.Cost,C.Priority,C.Zone,C.Arch)

            return RunningContainers
        
        except Exception as E:
            self.setDebug()
            self._recover()
            return self.getRunningContainers(ID)

    def getContainersFor(self,ID):
        try:
            self.cursor.execute("select C.CID from (Containers C join ZoneMembership Z on C.Zone = Z.ZID) join Nodes N on Z.NID = N.NID where N.`NID` = %s;",(ID,))
            AssignedContainers = self._colselect(self.cursor.fetchall(),0)

            if self.debug:
                print("I am assigned the following containers")
                for i in AssignedContainers:
                    C = self.queryContainerInfo(i)
                    print("-->",i,C.Name,C.Cost,C.Priority,C.Zone,C.Arch)

            return AssignedContainers
        
        except Exception as E:
            self.setDebug()
            self._recover()
            return self.getContainersFor(ID)
            
    
    def getMissingContainersFor(self,ID):
        try:
            #print("Get Missing")
            RunningContainers = self.getRunningContainers()
            #print(RunningContainers)

            AssignedContainers = self.getContainersFor(ID)

            #Determine which containers need to be started
            Missing = []
            
            for i in AssignedContainers:
                if i not in RunningContainers:
                    Missing.append(i)

            if self.debug:
                print("The Following Containers are missing and should be started")
                for i in Missing:
                    C = self.queryContainerInfo(i)
                    print("-->",i,C.Name,C.Cost,C.Priority,C.Zone,C.Arch)
            
            return Missing
        
        except Exception as E:
            self.setDebug()
            self._recover()
            return self.getMissingContainersFor(ID)

    def queryContainerInfo(self,ID):
        try:
            self.cursor.execute("select Name, Priority, Cost, Zone, Arch from Containers C where C.CID = %s",(ID,))
            Results = self.cursor.fetchall()

            if len(Results) == 0:
                return None
            else:
                return DataObjects.Container(ID,Results[0][0],Results[0][1],Results[0][2],Results[0][3],Results[0][4])
            
        except Exception as E:
            self.setDebug()
            self._recover()
            return self.queryContainerInfo(ID)


    def queryNodeInfo(self,ID):
        try:
            self.cursor.execute("select Name, Budget, Arch from Nodes N where N.NID = %s;",(ID,))
            Results = self.cursor.fetchall()

            if len(Results) == 0:
                return None
            else:
                return DataObjects.Node(ID,Results[0][0],Results[0][1],Results[0][2])
    
        except Exception as E:
            self.setDebug()
            self._recover()
            return self.queryNodeInfo(ID)
        

    def queryZoneMembers(self,ID):
        try:
            self.cursor.execute("select NID from ZoneMembership ZM where ZM.ZID = %s;",(ID,))
            Nodes = self._colselect(self.cursor.fetchall(),0)

            if self.debug:
                print("The Zone",ID,"Has the Following Nodes")
                for i in Nodes:
                    N = self.queryNodeInfo(i)
                    print("-->",N.ID,N.Name,N.Budget,N.Arch)

            return Nodes
        
        except Exception as E:
            self.setDebug()
            self._recover()
            return self.queryZoneMembers(ID)
        
    def queryRunningZoneMembers(self,ID,Interval):
        try:
            self.cursor.execute("select N.NID from ZoneMembership ZM join Nodes N on N.NID = ZM.NID where ZM.ZID = %s and (%s - N.LastSeen) < %s;",(ID,time.time(),Interval))
            Nodes = self._colselect(self.cursor.fetchall(),0)

            if self.debug:
                print("The Zone",ID,"Has the Following Running Nodes")
                for i in Nodes:
                    N = self.queryNodeInfo(i)
                    print("-->",N.ID,N.Name,N.Budget,N.Arch)

            return Nodes
        
        except Exception as E:
            self.setDebug()
            self._recover()
            return self.queryZoneMembers(ID)


    def queryZoneInfo(self,ID):
        try:
            self.cursor.execute("select Name from Zones Z where Z.ZID = %s;",(ID,))
            Results = self.cursor.fetchall()

            if len(Results) == 0:
                return None
            else:
                return DataObjects.Zone(ID,Results[0][0],self.queryZoneMembers(ID))
            
        except Exception as E:
            self.setDebug()
            self._recover()
            return self.queryZoneInfo(ID)
        
    def getContainerIDByName(self,Name):
        try:
            self.dbprint("Querying ID for Container Name",Name)

            self.cursor.execute("select C.CID from Containers C where C.Name = %s;",(Name,))
            Results = self.cursor.fetchall()

            if len(Results) == 0:
                return -1
            else:
                return Results[0][0]
        
        except Exception as E:
            self.setDebug()
            self._recover()
            return self.getContainerIDByName(Name)
        
    def getNodeIDByName(self,Name):
        try:
            self.dbprint("Querying ID for Node Name",Name)

            self.cursor.execute("select N.NID from Nodes N where N.Name = %s;",(Name,))
            Results = self.cursor.fetchall()

            if len(Results) == 0:
                return -1
            else:
                return Results[0][0]
            
        except Exception as E:
            self.setDebug()
            self._recover()
            return self.getNodeIDByName(Name)
        
    def getZoneIDByName(self,Name):
        try:
            self.dbprint("Querying ID for Zone Name",Name)

            self.cursor.execute("select Z.ZID from Zones Z where Z.Name = %s;",(Name,))
            Results = self.cursor.fetchall()

            if len(Results) == 0:
                return -1
            else:
                return Results[0][0]
        
        except Exception as E:
            self.setDebug()
            self._recover()
            return self.getZoneIDByName(Name)
        

    def getZoneUsageByNode(self,ID,Interval):
        try:
            self.cursor.execute("select CS.NID, sum(C.Cost)/N.Budget as `Usage` from (ContainerStatus CS join Containers C on CS.CID = C.CID) join Nodes N on CS.NID = N.NID where C.Zone = %s and  (%s - N.LastSeen) < %s group by CS.NID;",(ID,time.time(),Interval))
            
            
            Results = self.cursor.fetchall()

            OutDict = {}
            for line in Results:
                NID = line[0]
                Usage = line[1]
                OutDict[NID] = Usage

            RunningNodes = self.queryRunningZoneMembers(ID,Interval)
            for Node in RunningNodes:
                if Node not in OutDict:
                    OutDict[Node] = 0

            return OutDict
        
        except Exception as E:
            self.setDebug()
            self._recover()
            return self.getZoneUsageByNode(ID)
    
    def getNodeCostUsage(self,ID):
        try:
            self.cursor.execute("select sum(C.`Cost`) as TotalCost from (ContainerStatus CS join Containers C on CS.CID = C.CID) join Nodes N on CS.NID = N.NID where N.NID = %s;",(ID,))
            Results = self.cursor.fetchall()
            #print("COST",Results)

            if len(Results) == 0:
                return 0
            else:
                if Results[0][0] is None:
                    return 0
                
                return Results[0][0]

        except Exception as E:
            self.setDebug()
            self._recover()
            return self.getNodeCostUsage(ID)

    def removeRunningContainer(self,CID,NID):
        try:
            self.cursor.execute("delete from ContainerStatus where CID = %s and NID = %s;",(CID,NID))
            self.dbprint("Remove Running",CID,"on Node",NID)
        
        except Exception as E:
            self.setDebug()
            self._recover()
            self.removeRunningContainer(CID,NID)

    def addRunningContainer(self,CID,NID):
        try:
            self.cursor.execute("insert ignore into ContainerStatus(CID,NID) values (%s,%s);",(CID,NID))
            self.dbprint("Add Running",CID,"on Node",NID)
        
        except Exception as E:
            self.setDebug()
            self._recover()
            self.addRunningContainer(CID,NID)


    def updateNodeTime(self,NID):
        try:
            self.cursor.execute("update Nodes set LastSeen=%s where NID=%s;",(time.time(),NID))
            self.dbprint("Update Timestamp")

        except Exception as E:
            self.setDebug()
            self._recover()
            self.updateNodeTime(NID)

        

  
    