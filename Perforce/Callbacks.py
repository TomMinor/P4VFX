import maya.OpenMaya as api
import os

contactrootenv = "CONTACTROOT"
referenceCallback = None
submitCallback = None

def cleanupCallbacks():
    if referenceCallback:
        api.MCommandMessage.removeCallback(referenceCallback)

    if submitCallback:
        pass


def initCallbacks():
    global referenceCallback

    cleanupCallbacks()

    referenceCallback = api.MSceneMessage.addCheckFileCallback(
        api.MSceneMessage.kBeforeCreateReferenceCheck,
        referenceCallbackFunc)


def referenceCallbackFunc(inputBool, inputFile, *args):
    api.MScriptUtil.getBool(inputBool)

    print "Reference callback: Checking file {0}".format(os.environ[contactrootenv])

    try:
        contactrootpath = os.environ[contactrootenv]
    except KeyError as e:
        print "Error", e
        api.MScriptUtil.setBool(inputBool, True)
        return

    rawpath = inputFile.rawPath()
    rawname = inputFile.rawName()
    oldpath = rawpath
    if contactrootpath in rawpath:
        rawpath = rawpath.replace(
            contactrootpath, "${0}".format(contactrootenv))
        inputFile.setRawPath(rawpath)
        print "Remapped {0} -> {1}".format(oldpath, rawpath)

    if contactrootenv in rawpath:
        resolvedName = os.path.join(rawpath.replace("${0}".format(contactrootenv), contactrootpath), rawname)
        print rawpath, "->", resolvedName
        inputFile.overrideResolvedFullName(resolvedName)

    # print "RAWPATH", inputFile.rawPath()
    # print "RAWFULLNAME", inputFile.rawFullName()
    # print "RAWEXPANDEDPATH", inputFile.expandedPath()

    api.MScriptUtil.setBool(inputBool, True)
