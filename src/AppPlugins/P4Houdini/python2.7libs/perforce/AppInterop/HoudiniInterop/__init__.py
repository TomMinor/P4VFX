def validate():
	try:
		import hou
	except ImportError as e:
		return False
	return True

def setup():
	import interop