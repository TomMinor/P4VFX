from P4 import P4, P4Exception, OutputHandler
from sys import platform as _platform
import datetime
import pprint
import maya.cmds as cmds
import os

import perforce
reload(perforce)

try:
    test.close()
except:
    pass

PORT = "ssl:52.17.163.3:1666"
USER = "tminor"

test = perforce.Perforce(PORT, USER)
test.p4.connect()
test.login("***REMOVED***")
time = test.checkTicketExpiration()
print "%dh:%dm:%ds" % time

for user in test.p4.run("users"):
    for i in user:
        print i, ":", user[i]
    print ""
    
for client in test.p4.run_clients():
    for i in client:
        print i, ":", client[i]
        
print test.p4.fetch_client()
test.p4.run_sync("-f")
    
test.p4.set_env( 'P4CLIENT', 'tom-PC' )
    
print test.p4.client
print test.p4.port

test.p4.cwd = "D:/Perforce/contact_assets"


test.p4.run_have("workspace.mel")

localRev = test.p4.run_have("TestFile.txt")[0]['haveRev']
headRev = test.p4.run_files("TestFile.txt")[0]['rev']
print localRev, headRev
    
a = test.p4.run_add("TestFile.txt")
    
change = test.p4.fetch_change()
change._description = "p4test"
test.p4.run_submit(change, "-c")

test.p4.run_edit()

    
test.p4.cwd = "D:/Perforce/arse"
print test.p4.fetch_client()


""" Test Suite """
p4 = P4()
p4.port = PORT
p4.user = USER
p4.password = "contact_dev"
p4.connect()
p4.run_login("-a")

print p4.client

# Display all clients
clients = p4.run_clients()
for client in clients:
    if client['client'] == p4.client:
        p4.cwd = client['Root']
        print p4.cwd

# Find all files in client/depot
files = p4.run_have("...")
for file in files:
    print file
len(files)

for file in files:
    print "Revision: {0}\t\t\tClient: {1}\t\t\tDepot: {2}\t\t\tPath: {3}".format( file['haveRev'], file['clientFile'], file['depotFile'], file['path'] ) 

# Check if we're logged in
print p4.run_tickets()

# Add files
print p4.run_add( "TestFile.txt" )

# Un-Add file
try:
    p4.run_add( "TestFile5.txt" )
    print p4.run_add("Arse.txt")
    print p4.run_revert("TestFile5.txt")
except P4Exception as e:
    print e

# Query opened files
for file in p4.run_opened():
    print file

# Edit files
p4.run_edit("TestFile5.txt")

# Manually lock/unlock file/s
p4.run_lock("TestFile2.txt")
p4.run_unlock("TestFile2.txt")

# Submit changes with custom description

def submitChange(files, description):
    print files
    print description
    
    change = p4.fetch_change()

    #files = p4.run_have("...")
    #for x in files:
    #    print x['depotFile']
    change._description = description
    change._files = files
    p4.run_submit(change)

# Create workspace
def createWorkspace(rootPath, nameSuffix = None):
    spec = p4.fetch_workspace()

    # Figure out what platform we're on so we can add it to the client name
    platformType = "unknown"
    if _platform == "linux" or _platform == "linux2":
        platformType = "linux"
    elif _platform == "darwin":
        platformType = "osx"
    elif _platform == "win32":
        platformType = "win"
        
    client = "contact_{0}_{1}".format( p4.user, platformType )
    
    if nameSuffix:
        client += "_" + nameSuffix
    
    spec._client = client
    spec._root = os.path.join(str(rootPath), spec['Client'] )
    spec._view = [ '//depot/... //{0}/...'.format(spec['Client']) ]

    p4.set_env('P4CLIENT', spec['Client'])
    p4.cwd = spec['Root']
    
    p4.save_client(spec)
   
    print "Syncing new workspace..."
    p4.run_sync("...")
    print "Done!"
        
try:
    p4.cwd = p4.run_info()[0]['clientRoot']
except:
    print "No workspace found, creating default one"
    workspaceRoot = None
    while not workspaceRoot:
        workspaceRoot = cmds.fileDialog2(cap="Specify workspace root folder", fm=3)[0]
    createWorkspace(workspaceRoot, "test")

# Query file history & current revision
localRev = p4.run_have("TestFile.txt")[0]['haveRev']
headRev = p4.run_files("TestFile.txt")[0]['rev']
print localRev, headRev

changes = p4.run_changes("TestFile.txt")
for change in changes:
    print change['user'], "%s" % change['desc'],

fileInfo = p4.run_fstat(files[0]['clientFile'])

for change in changes:
    for key in change:
        print key + ": " + change[key],

# Error Handling test

files = p4.run("files", "...")
p4.run_edit("TestFile.txt")
p4.run_edit("TestFile2.txt")
p4.run_edit("TestFile3.txt")
p4.run_add("TestFile4.txt")
x = p4.run_opened("...")
for i in x:
    print i
for f in files:
	print "No Callback: %s\n" % (f['depotFile'])

p4.handler = MyOutputHandler()
p4.handler = None
files = p4.run("files", "arseshit")
print "Unprocessed : %d" % len(files)









