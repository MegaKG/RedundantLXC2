import lxc
import time

class lxcHandler:
    def __init__(self):
        pass

    def listContainers(self):
        out = []
        containers = lxc.list_containers()
        for i in containers:
            out.append(i)
        return out

    def listRunningContainers(self):
        Running = []
        for i in lxc.list_containers():
            C = lxc.Container(i)
            if C.running:
                Running.append(i)
        return Running

    def startContainer(self,Name):
        c = lxc.Container(Name)
        c.start()

    def stopContainer(self,Name):
        c = lxc.Container(Name)
        c.stop()

    def getStatus(self,Name):
        c = lxc.Container(Name)
        return c.running
    
    def awaitStart(self,Name,timeout=20):
        c = lxc.Container(Name)
        c.start()
        
        start = time.time()
        while True:
            now = time.time()
            if (now - start) > timeout:
                break
            else:
                if c.running:
                    #Started Successfully
                    return True
        #Timeout Exceeded
        return False
    
    def awaitStop(self,Name,timeout=20):
        c = lxc.Container(Name)
        c.stop()
        
        start = time.time()
        while True:
            now = time.time()
            if (now - start) > timeout:
                break
            else:
                if not c.running:
                    #Stopped Successfully
                    return True
        #Timeout Exceeded
        return False
