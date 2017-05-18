import sys
import os
import nuke

# sys.path.insert(0, os.path.abspath('.'))

for p in sys.path:
	nuke.tprint(p)

import perforce