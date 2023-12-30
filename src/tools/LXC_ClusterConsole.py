#!/usr/bin/env python3
import Database_handler as db
import time

HelpMenu = """
Redundant LXC Help:
- help, ? - This menu
- show - System Status
    - node
        - up - List online nodes
        - info - Lists node information
        - usage - Lists usage of online nodes
        - containers <ID> - Lists containers on specific node

    - container
        - flagged - List blocked containers
        - info - Container information
        - running - Online Containers

    - zone
        - info - List all Zones
        - nodes <ID> - Show nodes in Zone
        - containers <ID> - Show containers in Zone

- delete - Remove an Object and associated values
    - node
        - name <NAME>
        - id <ID>

    - container
        - name <NAME>
        - id <ID>

    - zone
        - name <NAME>
        - id <ID>

- add - Adds a new object
    - node - Create a new node
    - zone - Create a new zone
    - container - Create a new container

- assign <Node ID> <Zone ID> - Set Node Membership

- flag
    - set <Container ID> - Flag a container
    - unset <Container ID> - Unflag a container
"""

#'info':{'headers':[],'query':'','args':[]},
showQueries = {

    'node':{
         'up':{'headers':['ID','Name','Arch','Last Seen'],'query':'select Nodes.NID as `ID`, Nodes.`Name`, Nodes.`Arch`, FROM_UNIXTIME(NodeStatus.`LastSeen`) as `LastSeen` from Nodes natural join NodeStatus order by Nodes.NID;','args':[]},
         'info':{'headers':['ID','Name','Budget','Arch'],'query':'select * from Nodes order by Nodes.NID;','args':[]},
         'usage':{'headers':['ID','Name','Usage %'],'query':'select Nodes.NID as `ID`, Nodes.`Name`, 100 * (sum(Containers.`Cost`)/Nodes.`Budget`) as `Usage` from (Nodes join ContainerStatus on Nodes.NID = ContainerStatus.NID) join Containers on Containers.CID = ContainerStatus.NID group by Nodes.NID order by Nodes.NID;','args':[]},
         'containers':{'headers':['Container ID','Container Name','Cost'],'query':'select Containers.CID as `ID`, Containers.`Name`, Containers.`Cost` from (Nodes join ContainerStatus on Nodes.NID = ContainerStatus.NID) join Containers on Containers.CID = ContainerStatus.CID where Nodes.NID = %s;','args':[int]}
    },
    'container':{
         'flagged':{'headers':['ID','Name','Flagged Stamp'],'query':'select Containers.CID as `ID`, Containers.`Name`, FROM_UNIXTIME(FlaggedContainers.`Time`) as `FlaggedTime` from Containers natural join FlaggedContainers order by Containers.CID;','args':[]},
         'info':{'headers':['ID','Name','Priority','Cost','Zone ID','Arch'],'query':'select * from Containers;','args':[]},
         'running':{'headers':['Container','Node','Zone'],'query':'select Containers.`Name` as `Container`, Nodes.`Name` as `Node`, Zones.`Name` as `Zone`  from ((Containers join ContainerStatus on Containers.CID = ContainerStatus.CID) join Nodes on ContainerStatus.NID = Nodes.NID) join Zones on Containers.`Zone` = Zones.ZID order by Containers.`Name`;','args':[]}
    },
    'zone':{
         'info':{'headers':['ID','Name'],'query':'select * from Zones;','args':[]},
         'containers':{'headers':['Container ID','Container Name'],'query':'select Containers.CID as `ID`, Containers.`Name` from Containers join Zones on Containers.`Zone` = Zones.ZID where Zones.ZID = %s order by Containers.CID;','args':[int]},
         'nodes':{'headers':['Node ID','Node Name'],'query':'select Nodes.NID as `ID`, Nodes.`Name` from (Nodes natural join ZoneMembership) join Zones on Zones.ZID = ZoneMembership.ZID where Zones.ZID = %s order by Nodes.NID;','args':[int]}
    }
}

deleteQueries = {
    'node':{
        'name':{
            'headers':['Name'],
            'queries':[
                'delete from NodeStatus where NodeStatus.NID in (select Nodes.NID from Nodes where Nodes.`Name` like %s);',
                'delete from ContainerStatus where ContainerStatus.NID in (select Nodes.NID from Nodes where Nodes.`Name` like %s);',
                'delete from ZoneMembership where ZoneMembership.NID in (select Nodes.NID from Nodes where Nodes.`Name` like %s);',
                'delete from Nodes where Nodes.`Name` like %s;'
                ],
            'args':[str]
            },
        'id':{
            'headers':['Name'],
            'queries':[
                'delete from NodeStatus where NodeStatus.NID = %s;',
                'delete from ContainerStatus where ContainerStatus.NID = %s;',
                'delete from Nodes where Nodes.NID = %s;'
                ],
            'args':[int]
            }
    },
    'zone':{
        'name':{
            'headers':['Name'],
            'queries':[
                'delete from ZoneMembership where Zone.ZID in (select Zones.ZID from Zones where Zones.`Name` like %s);',
                'delete from Zones where Zones.`Name` like %s;'
                ],
            'args':[str]
            },
        'id':{
            'headers':['Name'],
            'queries':[
                'delete from ZoneMembership where ZoneMembership.ZID = %s;',
                'delete from Zones where Zones.ZID = %s;'
                ],
            'args':[int]
            }
    },
    'container':{
        'name':{
            'headers':['Name'],
            'queries':[
                'delete from ContainerStatus where ContainerStatus.CID in (select Containers.CID from Containers where Containers.`Name` like %s);',
                'delete from FlaggedContainers where FlaggedContainers.CID in (select Containers.CID from Containers where Containers.`Name` like %s);',
                'delete from Containers where Containers.`Name` like %s;'
                ],
            'args':[str]
            },
        'id':{
            'headers':['Name'],
            'queries':[
                'delete from ContainerStatus where ContainerStatus.CID = %s;',
                'delete from FlaggedContainers where FlaggedContainers.CID = %s;',
                'delete from Containers where Containers.CID = %s;'
                ],
            'args':[int]
            }
    }
}

addQueries = {
    'node':{'headers':['ID','Name','Budget','Arch'], 'args':[int, str, int, str], 'query':'insert into Nodes values (%s,%s,%s,%s);'},
    'zone':{'headers':['ID','Name'], 'args':[int, str], 'query':'insert into Zones values (%s,%s);'},
    'container':{'headers':['ID','Name','Priority','Cost','Zone','Arch'], 'args':[int, str, int, int, int, str], 'query':'insert into Zones values (%s,%s,%s,%s,%s,%s);' }
}

class dbadapter(db.database):
     def query(self,statement,*args):
          #print("Execute",statement,args)
          return self._runquery(statement,*args)

class application:
    def __init__(self,config):
        self.config = config

        #Initialise the Wrapper Objects
        self.database = dbadapter(
            config['Database']['Host'],
            config['Database']['Username'],
            config['Database']['Password'],
            config['Database']['Port'],
            config['Database']['Database']
        )
        print("INFO:","Init Database Connection")

    def _pad(self, Data,Length):
            out = str(Data)
            while len(out) < Length:
                out += ' '
            return out
    
    def _prettyDump(self,QueryResults,Columns=None):
        Data = QueryResults
        Headers = Columns

        if QueryResults == None:
             print("No Data")
             return

        if len(QueryResults) == 0:
             print("Empty Set")
             return

        spacer = ' | '

        #Prefill the column lengths
        ColumnLengths = []
        if Headers != None:
            for header in Headers:
                ColumnLengths.append(len(header))
        else:
             for cell in Data[0]:
                ColumnLengths.append(len(str(cell)))

        #Scan across the data
        for row in Data:
            for columnID, columnData in enumerate(row):
                if len(str(columnData)) > ColumnLengths[columnID]:
                    ColumnLengths[columnID] = len(str(columnData))

        #Generate a header
        TotalWidth = sum(ColumnLengths) + (len(ColumnLengths) * len(spacer))
        print('=' * (TotalWidth + 1))

        if Headers != None:
            strRow = ''
            for index in range(len(ColumnLengths)):
                strRow += self._pad(Headers[index],ColumnLengths[index]) + spacer

            print('| ' + strRow)
            print('=' * (TotalWidth + 1))

        for row in Data:
            strRow = ''
            for index in range(len(ColumnLengths)):
                strRow += self._pad(row[index],ColumnLengths[index]) + spacer
            print('| ' + strRow)

        print('=' * (TotalWidth + 1) + '\n')
        
        

        
        

    def showCommand(self,command):
         if len(command) >= 2:
            if command[0] in showQueries:
                if command[1] in showQueries[command[0]]:
                    argsOnly = command[2:]
                    args = []
                    for i, t in enumerate(showQueries[command[0]][command[1]]['args']):
                            args.append(t(argsOnly[i]))
                        
                    #print("Query",showQueries[command[0]][command[1]]['query'],*args)
                    Results = self.database.query(showQueries[command[0]][command[1]]['query'],*args)
                    #print("Returns",)
                    self._prettyDump(Results,showQueries[command[0]][command[1]]['headers'])

    def deleteCommand(self,command):
        if len(command) >= 2:
            if command[0] in deleteQueries:
                if command[1] in deleteQueries[command[0]]:
                    argsOnly = command[2:]
                    args = []
                    for i, t in enumerate(deleteQueries[command[0]][command[1]]['args']):
                            args.append(t(argsOnly[i]))

                    for query in deleteQueries[command[0]][command[1]]['queries']:
                        self.database.query(query,*args)

    def addCommand(self,command):
        if len(command) >= 1:
            if command[0] in addQueries:
                args = []
                for i, t in enumerate(addQueries[command[0]]['args']):
                        args.append(t(input('[ADD] ' + addQueries[command[0]]['headers'][i] + ' > ')))

                self.database.query(addQueries[command[0]]['query'],*args)

    def flagCommand(self,command):
         ID = int(command[1])
         if command[0] == 'set':
              self.database.query('insert into FlaggedContainers values (%s,NULL,%s);',ID,int(time.time()))
              print("Flagged Container ",ID)
         elif command[0] == 'unset':
              self.database.query('delete from FlaggedContainers where CID=%s;',ID)
              print("Unflagged Container ",ID)


    def run(self):
        try:
            while True:
                    command = input("RedunantLXC Global> ").split(' ')

                    if len(command) > 0:
                        try:
                            if command[0] in {'help','?'}:
                                print(HelpMenu)

                            elif command[0] == 'show':
                                self.showCommand(command[1:])

                            elif command[0] == 'delete':
                                self.deleteCommand(command[1:])

                            elif command[0] == 'add':
                                self.addCommand(command[1:])

                            elif command[0] == 'assign':
                                 NID = int(command[1])
                                 ZID = int(command[2])

                                 self.database.query('insert into ZoneMembership(ZID,NID) values (%s, %s);',ZID,NID)
                                 print("Added Membership")

                            elif command[0] == 'flag':
                                 self.flagCommand(command[1:])

                        except IndexError:
                            print("Missing Argument")

        except KeyboardInterrupt:
             pass
        except EOFError:
             pass
        


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

    app = application(config)
    app.run()
