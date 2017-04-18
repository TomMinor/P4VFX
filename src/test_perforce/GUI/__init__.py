# Workaround so we don't have to copy & paste the P4Python detection code in all submodules
import sys, os; sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
import test_perforce

import test_PerforceMenu