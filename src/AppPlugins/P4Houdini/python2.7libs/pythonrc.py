import sys
import os
sys.path.append( os.path.join( os.getenv('HOUDINI_USER_PREF_DIR'), 'python2.7libs', 'P4Houdini') )

import perforce
try:
    print "Adding Perforce Menu"
    perforce.init()
except Exception as e:
    sys.stderr.write( "Failed to load Perforce for Houdini: %s\n" % e)