import os
import sys
import re
import logging

import Perforce.Utils as Utils

# Import app specific utilities, maya opens scenes differently than nuke etc
# Are we in maya or nuke?
if re.match( "maya", os.path.basename( sys.executable ), re.I ):
	Utils.p4Logger().info("Configuring for Maya")
	from MayaUtils import *
elif re.match( "nuke", os.path.basename( sys.executable ), re.I ):
	Utils.p4Logger().info("Configuring for Nuke")
	from NukeUtils import *
else:
	Utils.p4Logger().warning("Couldn't find app configuration")
	raise ImportError("No supported applications found that this plugin can interface with")
