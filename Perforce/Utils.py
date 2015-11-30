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

from P4 import P4, P4Exception

p4_logger = logging.getLogger("Perforce")

#============================= Filesystem Procedures ===========================

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

def isPathInClientRoot(p4, path):
    if inDirectory(path, p4.cwd):
        return True
    else:
        p4_logger.warning("{0} not in client root".format(path))
        return False


def queryChangelists( p4, status = None):
    if not status:
        args = ["changes"]
    else:
        args = ["changes", "-s", status]

    try:
        return p4.run(args)
    except P4Exception as e:
        p4_logger.warning(e)
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

def submitChange(p4, files, description, keepCheckedOut = False):
    #change = p4.fetch_change()

    #change._description = description    
    
    p4_logger.info("Files Passed for submission = {0}".format(files))
    
    fullChangelist = p4.run_opened("-u", p4.user, "-C", p4.client, "...")

    fileList = []
    opened = [ p4.run_opened("-u", p4.user, "-C", p4.client, file)[0] for file in files ]
   
    changeFiles = [ entry['clientFile'] for entry in opened ]# change._files

    p4_logger.info("Changelist = {0}".format(changeFiles))

    for changeFile in changeFiles:
        if changeFile in files:
            fileList.append(changeFile)
        else:
            p4_logger.warning("File {0} ({1}) not in changelist".format(changeFile, p4.run_opened(changeFile)[0]['action']))
            
    p4_logger.info("Final changelist files = {0}".format(fileList)) 

    print [ x['clientFile'] for x in fullChangelist ]
    print [ x['clientFile'] for x in opened ]

    notSubmitted = list(set( [ x['clientFile'] for x in fullChangelist ] ) - set( [ x['clientFile'] for x in opened ] ))

    if notSubmitted:
        p4.run_revert("-k", notSubmitted)

    try:
        if keepCheckedOut:
            result = p4.run_submit("-r", "-d", description)
        else:
            result = p4.run_submit("-d", description)
        p4_logger.info(result)
    except P4Exception as e:
        p4_logger.warning(e)
        raise e

    #change._files = [ x['clientFile'] for x in opened ]

    #try:
    #    if keepCheckedOut:
    #        result = p4.run_submit(change, "-r")
    #    else:
    #        result = p4.run_submit(change)
    #    p4_logger.info(result)
    #except P4Exception as e:
    #    p4_logger.warning(e)
    #    raise e

def syncPreviousRevision(p4, file, revision, description):
    p4_logger.info(p4.run_sync("-f", "{0}#{1}".format(file, revision)))

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
            p4_logger.info( p4.run_revert("-k", file) )
        except P4Exception as e:
            errors.append(e)
        
        try:
            p4_logger.info( p4.run_edit("-c", changeId, file) )
        except P4Exception as e:
            errors.append(e)
            
        try:
            p4_logger.info( p4.run_sync("-f", file) )
        except P4Exception as e:
            errors.append(e)
        
        try:
            p4_logger.info( p4.run_resolve("-ay") )
        except P4Exception as e:
            errors.append(e)

        try:
            change = p4.fetch_change(changeId)
        except P4Exception as e:
            errors.append(e)
            
        try:
            p4_logger.info( p4.run_submit(change) )
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
                p4_logger.info("Deleting change {0} on client {1}".format(list['change'], list['client']))
                try:
                	p4.run_unlock("-c", list['change'])
                	p4.run_revert("-c", list['change'], "...")
            	except P4Exception as e:
            		pass
                p4_logger.info(p4.run_change("-d", list['change']))
            if not isUser:
                p4_logger.warning( "User {0} doesn't own change {1}, can't delete".format(p4.user, list['change']) )
            if not isClient:
                p4_logger.warning( "Client {0} doesn't own change {1}, can't delete".format(p4.client, list['change']) )
        except P4Exception as e:
            p4_logger.critical(e)

# Create workspace
def createWorkspace(p4, rootPath, nameSuffix = None):
    spec = p4.fetch_workspace()

    client = "contact_{0}_{1}".format( p4.user, platform.system().lower() )
    
    if nameSuffix:
        client += "_" + nameSuffix
    
    spec._client = client
    spec._root = os.path.join(str(rootPath), spec['Client'] )
    spec._view = [ '//depot/... //{0}/...'.format(spec['Client']) ]

    p4.client = spec['Client']
    if platform.system() == "Linux" or platform.system() == "Darwin":
        os.environ['P4CLIENT'] = p4.client
        saveEnvironmentVariable("P4CLIENT", p4.client)
    else:
        p4.set_env('P4CLIENT', p4.client)
        
    p4.cwd = spec['Root']
    
    p4_logger.info("Creating workspace {0}...".format(client))
    
    p4.save_client(spec)
   
    p4_logger.info("Syncing new workspace...")
    p4.run_sync("...")
    p4_logger.info("Done!")
