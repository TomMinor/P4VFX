import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os
# import platform
# def getSettingsPath():
#     user_dir = os.getenv("KATANA_USER_RESOURCE_DIRECTORY")
#     if user_dir:
#         return user_dir

#     if platform.system() == 'Windows':
#         if os.environ.get('HOME'):
#             home = os.environ['HOME']
#         else:
#             home = os.environ['USERPROFILE']
#         return os.path.join(home, '.katana')

#     elif platform.system() == 'Linux':
#         return os.path.expanduser('~/.katana')

#     elif platform.system() == 'Darwin':
#         return os.path.expanduser('~/.katana')

def getSettingsPath():
    if os.environ.get('HOME'):
        home = os.environ['HOME']
    else:
        home = os.environ['USERPROFILE']
    return os.path.join(home, '.katana')

import sys
sys.path.append(os.path.join(getSettingsPath(), 'P4Katana'))

# Tell qtpy to use PyQt
os.environ['QT_API'] = 'pyqt4'
os.environ['ETS_TOOLKIT'] = 'qt4'


# try:
# 	import perforce
# except Exception as e:
#     logger.error( traceback.format_exc() )

# try:
#     logger.info("Adding Perforce Menu...")
#     perforce.init()
# except Exception as e:
#     logger.error( "Failed to load Perforce for Katana: %s\n" % e )
#     logger.error( traceback.format_exc() )