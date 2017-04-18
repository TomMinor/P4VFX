try:
	import P4
except ImportError:
	import sys
	import os
	import platform

	if platform.system() == 'Linux':
		p4api = os.path.abspath( os.path.join(os.path.dirname(__file__),'../../P4API/linux') )
	elif platform.system() == 'Windows':
		p4api = os.path.abspath( os.path.join(os.path.dirname(__file__),'../../P4API/windows'))
	else:
		raise RuntimeError('Can\'t load P4API for %s' % platform.system())

	sys.path.append(p4api)

	try:
		import P4
	except ImportError as e:
		raise


import perforce

# from GUI import PerforceMenuTests