import platform
import psutil

class node:
    def __init__(self):
        pass

    def getHostname(self):
        return platform.node()
    
    def getProcessorUsage(self):
        return psutil.cpu_percent(10)
    
    def getMemoryUsage(self):
        return psutil.virtual_memory().percent
    
    def getArchitecture(self):
        return platform.machine()
