import mysql.connector as mc
import time

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
        #self.setDebug()

    def setDebug(self):
        self.debugStart = time.time()
        self.debug = True

    def resetDebug(self):
        if self.debug:
            if (time.time() - self.debugStart) > 60:
                print("Clear Debug")
                self.debug = False

    def dbprint(self,*n):
        if self.debug:
            print(*n)
            self.resetDebug()

    def _colselect(self,Data,index):
        out = []
        for i in Data:
            out.append(i[index])
        return out
    
    def _runquery(self,Statement, *Args):
        self.dbprint("Run Statement",Statement,Args)
        #print("--> Run Statement",Statement,Args)
        try:
            #Execute the statement
            self.cursor.execute(Statement,tuple(Args))
            Results = self.cursor.fetchall()
            self.db.commit()

            #print("+--- Returns -- >",Results)

            #Fetch the Results
            return Results

        except Exception as E:
            self.setDebug()
            self._recover()
            self._runquery(Statement, *Args)

    