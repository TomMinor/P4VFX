import maya.OpenMaya as api
import maya.cmds as cmds
import os

import Utils

contactrootenv = "CONTACTROOT"
referenceCallback = None
saveCallback = None

def validateSubmit():
    print "Validating submission"
    return 0

def cleanupCallbacks():
    if referenceCallback:
        try:
            api.MCommandMessage.removeCallback(referenceCallback)
        except RuntimeError as e:
            print e

    if saveCallback:
        try:
            api.MCommandMessage.removeCallback(saveCallback)
        except RuntimeError as e:
            print e


def initCallbacks():
    global referenceCallback
    global saveCallback

    cleanupCallbacks()

    referenceCallback = api.MSceneMessage.addCheckFileCallback(
        api.MSceneMessage.kBeforeCreateReferenceCheck,
        referenceCallbackFunc)

    saveCallback = api.MSceneMessage.addCallback(
        api.MSceneMessage.kAfterSave,
        saveCallbackFunc)


def saveCallbackFunc(*args):
    fileName = cmds.file(q=True, sceneName=True)

    if ".ma" in fileName:
        print "Save callback: Checking file {0} for education flags".format(fileName)
        Utils.removeStudentTag(fileName)

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
