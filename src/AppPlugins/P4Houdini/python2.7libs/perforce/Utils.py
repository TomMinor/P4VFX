import os
import traceback
import ntpath
import subprocess
import string
import re
import platform
import sys
import logging
import stat
import fileinput
import traceback

from P4 import P4, P4Exception

def p4Logger():
    return logging.getLogger("Perforce")

def importClass(modulePath, className):
    mod = __import__(modulePath, fromlist=[className])
    return getattr(mod, className)


#============================= Filesystem Procedures ===========================
def queryFilesInDirectory(rootDir):
	allFiles = []
	for root, dirnames, filenames in os.walk( rootDir ):
		currentDir = ""
		if dirnames:
			currentDir = dirnames[0]

		fullPath = os.path.join(root, currentDir)

		for file in filenames:
			allFiles.append( os.path.join(fullPath, file) )

	return allFiles

def makeDirectory(path):
	if not os.path.exists(path):
		os.mkdir(path)
	return path

def makeEmptyFile(path):
    try:
        open(path, 'a').close()
    except IOError as e:
        print e

def makeEmptyDirectory(path):
	if not os.path.exists(path):
		os.mkdir(path)
	makeEmptyFile( os.path.join(path, ".place-holder") )
	return path

def createAssetFolders(root, assetName):
    # @ToDo Make this more generic (or remove completely)
    rootDir = os.path.join(root, "assets")
    assetsDir = os.path.join(rootDir, assetName)

    makeDirectory( rootDir )
    makeDirectory( assetsDir )
    makeEmptyDirectory( os.path.join(assetsDir, "lookDev") )
    makeEmptyDirectory( os.path.join(assetsDir, "modelling") )
    makeEmptyDirectory( os.path.join(assetsDir, "rigging") )
    makeEmptyDirectory( os.path.join(assetsDir, "texturing") )

    return assetsDir

def createShotFolders(root, shotName, shotNumInput):
    # @ToDo Make this more generic (or remove completely)
    rootDir = os.path.join(root, "shots")
    shotsDir = os.path.join(rootDir, shotName)
    shotNum = "{0}0".format( format(shotNumInput, '02') )
    shotNumberDir = os.path.join( shotsDir, "{0}_sh_{1}".format(shotName, shotNum) )

    makeDirectory( rootDir )
    makeDirectory( shotsDir )
    shot = makeDirectory( shotNumberDir )

    #Cg
    cg = makeDirectory( os.path.join(shot, "cg") )

    houdini = makeDirectory( os.path.join(cg, "houdini") )
    makeEmptyDirectory( os.path.join(houdini, "scenes") )

    maya = makeDirectory( os.path.join(cg, "maya") )
    makeEmptyDirectory( os.path.join(maya, "images") )
    makeEmptyDirectory( os.path.join(maya, "scenes") )

    makeEmptyDirectory( os.path.join(shot, "comp") )
    makeEmptyDirectory( os.path.join(shot, "dailies") )
    makeEmptyDirectory( os.path.join(shot, "delivery") )
    makeEmptyDirectory( os.path.join(shot, "plates") )

    return shotNumberDir

def removeReadOnlyBit(files):
    for file in files:
        fileAtt = os.stat(file)[0]
        if (not fileAtt & stat.S_IWRITE):
           # File is read-only, so make it writeable
           os.chmod(file, stat.S_IWRITE)
        else:
           # File is writeable, so make it read-only
           #os.chmod(myFile, stat.S_IREAD)
           pass

def addReadOnlyBit(files):
    for file in files:
        fileAtt = os.stat(file)[0]
        if (not fileAtt & stat.S_IWRITE):
           # File is read-only, so make it writeable
           #os.chmod(file, stat.S_IWRITE)
           pass
        else:
           # File is writeable, so make it read-only
           os.chmod(file, stat.S_IREAD)

def open_file(filename):
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener ="open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])

def queryFileExtension(filePath, extensions = [] ):
    if not extensions:
        return False
        
    extensions = [ ext.lower() for ext in extensions ]
        
    fileExt = os.path.splitext(filePath)[1]
    fileExt = fileExt.lower()
    
    return fileExt in extensions

def isPathInClientRoot(p4, path):
    if inDirectory(path, p4.cwd):
        return True
    else:
        p4Logger().warning("{0} not in client root".format(path))
        return False

def inDirectory(file, directory):
    #make both absolute    
    directory = os.path.join(os.path.realpath(directory), '')
    file = os.path.realpath(file)

    #return true, if the common prefix of both is equal to directory
    #e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return (os.path.commonprefix([file, directory]) == directory) or (os.path.abspath(file) == os.path.abspath(directory))
