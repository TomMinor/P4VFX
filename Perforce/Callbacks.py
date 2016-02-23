import maya.OpenMaya as api
import os

contactrootenv = "CONTACTROOT"
referenceCallback = None


def cleanupCallbacks():
    if referenceCallback:
        api.MCommandMessage.removeCallback(referenceCallback)


def initCallbacks():
    global referenceCallback

    cleanupCallbacks()

    referenceCallback = api.MSceneMessage.addCheckFileCallback(
        api.MSceneMessage.kBeforeCreateReferenceCheck,
        referenceCallbackFunc)


def referenceCallbackFunc(inputBool, inputFile, *args):
    api.MScriptUtil.getBool(inputBool)

    try:
        contactrootpath = os.environ[contactrootenv]
        print os.environ[contactrootenv]
    except KeyError as e:
        print "Error", e
        api.MScriptUtil.setBool(inputBool, True)
        return

    rawpath = inputFile.rawPath()
    oldpath = rawpath
    if contactrootpath in rawpath:
        rawpath = rawpath.replace(
            contactrootpath, "${0}".format(contactrootenv))
        inputFile.setRawPath(rawpath)
        print "Remapped {0} -> {1}".format(oldpath, rawpath)

    # print "RAWPATH", inputFile.rawPath()
    # print "RAWFULLNAME", inputFile.rawFullName()
    # print "RAWEXPANDEDPATH", inputFile.expandedPath()

    api.MScriptUtil.setBool(inputBool, True)
