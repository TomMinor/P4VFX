import unittest
import logging

logging.basicConfig(level=logging.DEBUG)

def setupEnvironment():
    try:
        import P4
    except ImportError:
        import sys
        import os
        import platform

        if platform.system() == 'Linux':
            p4api = os.path.abspath(os.path.join(
                os.path.dirname(__file__), '../../P4API/linux'))
        elif platform.system() == 'Windows':
            p4api = os.path.abspath(os.path.join(
                os.path.dirname(__file__), '../../P4API/windows'))
        else:
            raise RuntimeError('Can\'t load P4API for %s' % platform.system())

        sys.path.append(p4api)

        try:
            import P4
        except ImportError as e:
            raise

setupEnvironment()


from P4 import P4, P4Exception
from perforce.PerforceUtils import SetupConnection
def TestingEnvironment():
    p4 = P4()
    p4.connect()

    return p4