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
def removeStudentTag(fileName):
    try:
        with open(fileName, "r") as f:
            lines = f.readlines()
    except IOError as e:
        print e
        return 1

    try:
        with open(fileName, "w") as f:
            for line in lines:
                if "fileInfo" in line:
                    if "education" in line:
                        print "Removing education flag from file {0}".format(fileName)
                    elif "student" in line:
                        print "Removing student flag from file {0}".format(fileName)
                else:
                    f.write(line)
    except IOError as e:
        print e
        return 1

    return 0

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

def saveEnvironmentVariable( var, value ):
    os.system('bash -c \'echo "export {0}={1}" >> ~/.bashrc\''.format(var, value))
    os.system('bash -c \'source ~/.bashrc\'')


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

def inDirectory(file, directory):
    #make both absolute    
    directory = os.path.join(os.path.realpath(directory), '')
    file = os.path.realpath(file)

    #return true, if the common prefix of both is equal to directory
    #e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return (os.path.commonprefix([file, directory]) == directory) or (os.path.abspath(file) == os.path.abspath(directory))

#============================= Perforce Procedures ===========================

def setupConnection(p4):
    if not p4.connected():
        p4Logger().info('Connecting to server...')
        p4.connect()

    try:
        p4.fetch_client()['Root']
    except P4Exception as e:
        p4Logger().info('Attempting to login...')
        try:
            from perforce.GUI import LoginWindow
            LoginWindow.setP4Password(p4)
        except P4Exception as e:
            p4Logger().warning('Couldn\'t login to server')
            raise

    if p4.p4config_file == 'noconfig':
        Utils.loadP4Config(p4)

    p4Logger().info('Connected to server!')

def loadP4Config(p4):
    # Stupid bug (Windows only I hope)
    if p4.p4config_file == "noconfig":
        configpath = os.environ['P4CONFIG'].replace('\\', '/') 
        print os.path.isfile( configpath )
        print os.path.isfile("C:/Users/tom/.p4config")
        if os.path.isfile( os.environ['P4CONFIG'].replace('\\', '/') ):
            p4Logger().info("Reading from config file at {0}".format(os.environ['P4CONFIG']) )
            with open( os.environ['P4CONFIG'] ) as file:
                for line in file:
                    key, value = line.split("=")
                    p4Logger().info("Setting {0}={1}".format(key,value))
                    p4.set_env(key, value)

# ToDo rewrite this AWFUL function
def writeToP4Config(config, key, value):
    return

    found = False
    fileinput.close()
    
    p4Logger().info("Writing {0}:{1} to config {2}".format(key, value, config))

    if config == 'noconfig':
        raise RuntimeError('No configuration file found (%s)' % config)

    try:
        for line in fileinput.input(config, inplace=True):
            result = line
            resultSplit = line.split("=")
            
            if len(resultSplit) == 2:
                _key, _value = resultSplit
                if _key == key:
                    result = "{0}={1}\n".format( key, value )
                    found = True
                    
            print "\n" + result + "\n",
            
        if not found:
            with open(config, "a") as file:
                file.write( "{0}={1}\n".format( key, value ) )
    except Exception as e:
        p4Logger().error(e)


def isPathInClientRoot(p4, path):
    if inDirectory(path, p4.cwd):
        return True
    else:
        p4Logger().warning("{0} not in client root".format(path))
        return False


def queryChangelists( p4, status = None):
    if not status:
        args = ["changes"]
    else:
        args = ["changes", "-s", status]

    try:
        return p4.run(args)
    except P4Exception as e:
        p4Logger().warning(e)
        raise e

def parsePerforceError(e):
    eMsg = str(e).replace("[P4#run]", "")
    idx = eMsg.find('\t')
    firstPart = " ".join(eMsg[0:idx].split())
    firstPart = firstPart[:-1]
    
    secondPart = eMsg[idx:]
    secondPart = secondPart.replace('\\n', '\n')
    secondPart = secondPart.replace('"', '')
    secondPart = " ".join(secondPart.split())
    secondPart = secondPart.replace(' ', '', 1) # Annoying space at the start, remove it
    
    eMsg = "{0}\n\n{1}".format(firstPart, secondPart)

    type = "info"
    if "[Warning]" in str(e):
        eMsg = eMsg.replace("[Warning]:", "")
        type = "warning"
    elif "[Error]" in str(e):
        eMsg = eMsg.replace("[Error]:", "")
        type = "error"
    
    return eMsg, type

def submitChange(p4, files, description, callback, keepCheckedOut = False):
    # Shitty method #1
    p4Logger().info("Files Passed for submission = {0}".format(files))
    
    print "Opened ", p4.run_opened("...")

    fullChangelist = p4.run_opened("-u", p4.user, "-C", p4.client, "...")
    
    if not fullChangelist:
        raise P4Exception("File changelist is empty")

    fileList = []
    opened = [ p4.run_opened("-u", p4.user, "-C", p4.client, file)[0] for file in files ]
   
    changeFiles = [ entry['clientFile'] for entry in opened ]# change._files

    p4Logger().info("Changelist = {0}".format(changeFiles))

    for changeFile in changeFiles:
        if changeFile in files:
            fileList.append(changeFile)
        else:
            p4Logger().warning("File {0} ({1}) not in changelist".format(changeFile, p4.run_opened(changeFile)[0]['action']))
            
    p4Logger().info("Final changelist files = {0}".format(fileList)) 

    print [ x['clientFile'] for x in fullChangelist ]
    print [ x['clientFile'] for x in opened ]

    notSubmitted = list(set( [ x['clientFile'] for x in fullChangelist ] ) - set( [ x['clientFile'] for x in opened ] ))

    if notSubmitted:
        p4.run_revert("-k", notSubmitted)

    try:
        p4.progress = callback 
        p4.handler = callback

        if keepCheckedOut:
            result = p4.run_submit("-r", "-d", description, progress=callback, handler=callback)
        else:
            result = p4.run_submit("-d", description, progress=callback, handler=callback)
        p4Logger().info(result)
    except P4Exception as e:
        p4Logger().warning(e)
        raise e

    p4.progress = None
    p4.handler = None

    # change = p4.fetch_change()

    # change._description = description    

    # change._files = changeFile

    # try:
    #     if keepCheckedOut:
    #         result = p4.run_submit(change, "-r")
    #     else:
    #         result = p4.run_submit(change)
    #     p4Logger().info(result)
    # except P4Exception as e:
    #     p4Logger().warning(e)
    #     raise e

def syncPreviousRevision(p4, file, revision, description):
    p4Logger().info(p4.run_sync("-f", "{0}#{1}".format(file, revision)))

    change = p4.fetch_change()
    change._description = description

    result = p4.save_change(change)
    r = re.compile("Change ([1-9][0-9]*) created.")
    m = r.match(result[0])
    changeId = "0"
    if m:
        changeId = m.group(1)

    # Terrible exception handling but I need all the info I can for this to be artist proof
    try:
        errors = []
        
        # Try to remove from changelist if we have it checked out
        try:
            p4Logger().info( p4.run_revert("-k", file) )
        except P4Exception as e:
            errors.append(e)
        
        try:
            p4Logger().info( p4.run_edit("-c", changeId, file) )
        except P4Exception as e:
            errors.append(e)
            
        try:
            p4Logger().info( p4.run_sync("-f", file) )
        except P4Exception as e:
            errors.append(e)
        
        try:
            p4Logger().info( p4.run_resolve("-ay") )
        except P4Exception as e:
            errors.append(e)

        try:
            change = p4.fetch_change(changeId)
        except P4Exception as e:
            errors.append(e)
            
        try:
            p4Logger().info( p4.run_submit(change) )
        except P4Exception as e:
            errors.append(e)
        
        if errors:
            raise tuple(errors)
    except P4Exception as e:
        displayErrorUI(e)
        return False
    return True

def forceChangelistDelete(p4, lists):
    for list in lists:
        try:
            isUser = (list['user'] == p4.user) 
            isClient = (list['client'] == p4.client)
            
            if isUser and isClient:
                p4Logger().info("Deleting change {0} on client {1}".format(list['change'], list['client']))
                try:
                	p4.run_unlock("-c", list['change'])
                	p4.run_revert("-c", list['change'], "...")
            	except P4Exception as e:
            		pass
                p4Logger().info(p4.run_change("-d", list['change']))
            if not isUser:
                p4Logger().warning( "User {0} doesn't own change {1}, can't delete".format(p4.user, list['change']) )
            if not isClient:
                p4Logger().warning( "Client {0} doesn't own change {1}, can't delete".format(p4.client, list['change']) )
        except P4Exception as e:
            p4Logger().critical(e)

# Create workspace
def createWorkspace(p4, rootPath, nameSuffix = None):
    spec = p4.fetch_workspace()

    client = "contact_{0}_{1}".format( p4.user, platform.system().lower() )
    
    if nameSuffix:
        client += "_" + nameSuffix
    
    spec._client = client
    spec._root = os.path.join(str(rootPath), spec['Client'] )
    spec._view = [ '//depot/... //{0}/...'.format(spec['Client']) ]
    spec._host = ""

    p4.client = spec['Client']

    # REALLY make sure we save the P4CLIENT variable
    if platform.system() == "Linux" or platform.system() == "Darwin":
        os.environ['P4CLIENT'] = p4.client
    else:
        p4.set_env('P4CLIENT', p4.client)
        
    p4.cwd = spec['Root']
    
    p4Logger().info("Creating workspace {0}...".format(client))
    
    p4.save_client(spec)

    p4Logger().info("Syncing new workspace...")
    
    try:
        p4.run_sync("...")
        p4Logger().info("Sync Done!")
    except P4Exception as e:
        p4Logger().info("Sync failed, probably because the depot is empty")

    if not os.path.exists(spec['Root']):
        os.makedirs(spec['Root'])

    p4Logger().info("Writing to config...")
    writeToP4Config(p4.p4config_file, "P4CLIENT", p4.client)
    p4Logger().info("Done!")