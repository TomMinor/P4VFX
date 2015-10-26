import maya.cmds as cmds
import subprocess
import PerforceIntegration

home = "/home/i7245143"
P4EXE = home  + "/local/bin/p4"

class Perforce:
    def __init__(self):
        pass
        
    def addFile(filePath);
        print subprocess.check_output([P4EXE, "add", filePath])
        
    def revertFile(filePath):
        print subprocess.check_output([P4EXE, "revert", filePath])
        
    def checkoutFile(filePath):
        print subprocess.check_output([P4EXE, "edit", filePath])
        
class PerforceWin(Perforce):
    def __init__(self):
        pass

class PerforceLinux(Perforce):
    def __init__(self):
        pass
        

print subprocess.check_output([P4EXE, "edit", home + "/Perforce/tminor_uni_ws/TestFile3.txt"])