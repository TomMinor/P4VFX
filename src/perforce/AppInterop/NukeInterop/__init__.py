def validate():
	try:
		import nuke
	except ImportError as e:
		return False
	return True

def setup():
	import interop