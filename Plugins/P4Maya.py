import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx

kPluginCmdName = "MayaP4Integration"

import Perforce
reload(Perforce)

# Creator
def cmdCreator():
    return OpenMayaMPx.asMPxPtr( scriptedCommand() )
    
# Initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        print "Adding Perforce Menu"
        Perforce.init()
    except:
        sys.stderr.write( "Failed to register command: %s\n" % kPluginCmdName )
        raise

# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        print "Removing Perforce Menu"
        Perforce.close()
    except Exception as e:
        print e
        sys.stderr.write( "Failed to unregister command: %s\n" % kPluginCmdName )