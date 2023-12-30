CreateStatements = [
            "create table if not exists Nodes(`NID` INT NOT NULL, `Name` VARCHAR(64) NOT NULL, `Budget` INT NOT NULL, `Arch` VARCHAR(16), PRIMARY KEY(`NID`));",
            "create table if not exists Zones(`ZID` INT NOT NULL, `Name` VARCHAR(64) NOT NULL, PRIMARY KEY(`ZID`));",
            "create table if not exists Containers(`CID` INT NOT NULL, `Name` VARCHAR(64) NOT NULL, `Priority` INT NOT NULL, `Cost` INT NOT NULL, `Zone` INT NOT NULL, `Arch` VARCHAR(16), PRIMARY KEY(`CID`), FOREIGN KEY(`Zone`) REFERENCES Zones(`ZID`));",
            "create table if not exists ZoneMembership(`ZID` INT NOT NULL, `NID` INT NOT NULL, PRIMARY KEY(`ZID`,`NID`), FOREIGN KEY(`ZID`) REFERENCES Zones(`ZID`), FOREIGN KEY(`NID`) REFERENCES Nodes(`NID`));",
            "create table if not exists ContainerStatus(`NID` INT NOT NULL, `CID` INT NOT NULL, PRIMARY KEY(`CID`), FOREIGN KEY(`NID`) REFERENCES Nodes(`NID`), FOREIGN KEY(`CID`) REFERENCES Containers(`CID`)) ENGINE=MEMORY;",
            "create table if not exists FlaggedContainers(`CID` INT NOT NULL, `NID` INT, `Time` BIGINT(255) NOT NULL, PRIMARY KEY(`CID`), FOREIGN KEY(`CID`) REFERENCES Containers(`CID`));",
            "create table if not exists NodeStatus(`NID` INT NOT NULL, `LastSeen` BIGINT(255) NOT NULL, PRIMARY KEY(`NID`), FOREIGN KEY(`NID`) REFERENCES Nodes(`NID`)) ENGINE=MEMORY;"
        ]


CleanNodes = "delete from NodeStatus where (%s - NodeStatus.LastSeen) > %s;"
CleanStatus = "delete from ContainerStatus where ContainerStatus.NID not in (select NodeStatus.NID from NodeStatus);"

ContainerInfo = "select Name, Priority, Cost, Zone, Arch from Containers C where C.CID = %s"
NodeInfo = "select Name, Budget, Arch from Nodes N where N.NID = %s;"
ZoneInfo = "select Name from Zones Z where Z.ZID = %s;"

ZoneMembers = "select NID from ZoneMembership ZM where ZM.ZID = %s;"
ZonesForNode = "select ZID from ZoneMembership ZM where ZM.NID = %s;"
ZoneRunningMembers = "select N.NID from ZoneMembership ZM join Nodes N on N.NID = ZM.NID where ZM.ZID = %s;"

ContainerIDByName = "select C.CID from Containers C where C.Name = %s;"
NodeIDByName = "select N.NID from Nodes N where N.Name = %s;"
ZoneIDByName = "select Z.ZID from Zones Z where Z.Name = %s;"

AddRunning = "insert ignore into ContainerStatus(CID,NID) values (%s,%s);"
RemoveRunning = "delete from ContainerStatus where CID = %s and NID = %s;"

UpdateNode = "replace into NodeStatus(`NID`,`LastSeen`) values (%s,%s);"
FlagContainer = "insert ignore into FlaggedContainers(CID,NID,Time) values (%s,%s,%s);"

FindMissingContainersForZone = """
select Containers.CID from 
Containers join Zones on Containers.`Zone` = Zones.ZID
where Containers.CID not in
(select ContainerStatus.CID from ContainerStatus)
and Zones.ZID=%s and Containers.`Arch`=%s
and Containers.CID not in (select FlaggedContainers.CID from FlaggedContainers);
"""

UsageAndBudgetForNode = """
select Costs.`Used`, Nodes.`Budget` from Nodes
join (select ContainerStatus.NID as NID, sum(Containers.Cost) as `Used` from ContainerStatus join Containers on Containers.CID = ContainerStatus.CID group by ContainerStatus.NID) as Costs
on Costs.NID = Nodes.NID
where Nodes.NID=%s;
"""

ContainersAssignedToNode = """
select ContainerStatus.CID from ContainerStatus where ContainerStatus.NID=%s
and ContainerStatus.CID 
not in (select FlaggedContainers.CID from FlaggedContainers);
"""

ContainersNotAssignedToNode = """
select ContainerStatus.CID from ContainerStatus where not(ContainerStatus.NID=%s)
and ContainerStatus.CID 
not in (select FlaggedContainers.CID from FlaggedContainers);
"""

ContainersAvailableToNode = """
select Containers.CID from Containers join ZoneMembership on Containers.Zone = ZoneMembership.ZID 
where ZoneMembership.NID = %s and Containers.CID not in (select FlaggedContainers.CID from FlaggedContainers);
"""

ZoneUsage = """
select Nodes.NID, Nodes.`Budget`,Costs.`Used` from (Nodes
join (select ContainerStatus.NID as NID, sum(Containers.Cost) as `Used` from ContainerStatus join Containers on Containers.CID = ContainerStatus.CID group by ContainerStatus.NID) as Costs
on Costs.NID = Nodes.NID) join ZoneMembership on Nodes.NID = ZoneMembership.NID where ZoneMembership.ZID = %s
union
select NodeStatus.NID, Nodes.`Budget`, 0 as `Used` from Nodes join NodeStatus on Nodes.NID = NodeStatus.NID where Nodes.NID not in (select ContainerStatus.NID from ContainerStatus);
;
"""

ZoneContainersRunning = """
select ContainerStatus.CID from ContainerStatus join Containers on ContainerStatus.CID = Containers.CID 
where Containers.Zone = %s;
"""