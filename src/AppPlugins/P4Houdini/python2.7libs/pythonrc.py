import sys
import os
prefs = os.getenv("HOUDINI_USER_PREF_DIR")
sys.path.append( os.path.join( prefs, 'scripts', 'python', 'P4Houdini') )

import perforce
try:
    print "Adding Perforce Menu"
    perforce.init()
except Exception as e:
    sys.stderr.write( "Failed to load Perforce for Houdini: %s\n" % e)