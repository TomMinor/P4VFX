import perforce.Utils as Utils

def validate():
	try:
		import maya.standalone
	except ImportError as e:
		return False
	return True

def setup():
	import interop