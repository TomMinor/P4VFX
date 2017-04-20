import imp
import os
import sys
import re
import logging
import glob

import perforce.Utils as Utils

def loadInteropModule(name, path):
    file, filename, data = imp.find_module( name, [cwd])
    mod = imp.load_module(name, file, filename, data)

    return name, mod


cwd = os.path.dirname(os.path.realpath(__file__))

modules = glob.glob(os.path.join(cwd,'*'))

# Only allow __init__.py based modules (in folders) to make things simpler
modules = filter(lambda x: not x.endswith('.py'), modules)
modules = filter(lambda x: not x.endswith('.pyc'), modules)

# Get only the relative directory paths
modules = [os.path.basename(x) for x in modules]

for module in modules:
    name, mod = loadInteropModule(module, cwd)

    try:
        if not mod.validate():
            continue
    except AttributeError as e:
        Utils.p4Logger().debug('%s has no validate() method, skipping' % name)
        continue

    Utils.p4Logger().info("Configuring for %s" % name)
    mod.setup()
    submodule = getattr(mod, 'interop')
    interop = getattr(submodule, name)
    break
else:
    interop = None


# interop = __import__('perforce.interop.MayaInterop', fromlist=['MayaInterop'])
# print getattr(interop, 'MayaInterop')


# # Import app specific utilities, maya opens scenes differently than nuke etc
# # Are we in maya or nuke?
# if re.match("maya", os.path.basename(sys.executable), re.I):
#     Utils.p4Logger().info("Configuring for Maya")
#     interop = Utils.importClass('perforce.interop.MayaInterop', 'MayaInterop')

# elif re.match("nuke", os.path.basename(sys.executable), re.I):
#     Utils.p4Logger().info("Configuring for Nuke")
#     interop = Utils.importClass('perforce.interop.NukeInterop', 'NukeInterop')

# elif in_unittest:
#     Utils.p4Logger().info("Configuring for testing")
#     interop = Utils.importClass('perforce.interop.TestInterop', 'TestInterop')

# else:
#     Utils.p4Logger().warning("Couldn't find app configuration")
#     raise ImportError(
#         "No supported applications found that this plugin can interface with")

