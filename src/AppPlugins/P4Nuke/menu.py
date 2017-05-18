import sys
import traceback
import nuke
import perforce

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    logger.info("Adding Perforce Menu...")
    perforce.init()
except Exception as e:
    logger.error( "Failed to load Perforce for Nuke: %s\n" % e )
    logger.error( traceback.format_exc() )