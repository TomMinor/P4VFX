import os
import sys
import re
import logging

p4_logger = logging.getLogger("Perforce")

# Import app specific utilities, maya opens scenes differently than nuke etc
# Are we in maya or nuke?
if re.match( "maya", os.path.basename( sys.executable ), re.I ):
	p4_logger.info("Configuring for Maya")
	from MayaUtils import *
elif re.match( "nuke", os.path.basename( sys.executable ), re.I ):
	p4_logger.info("Configuring for Nuke")
	from NukeUtils import *
else:
	p4_logger.warning("Couldn't find app configuration")
	raise ImportError("No supported applications found that this plugin can interface with")
