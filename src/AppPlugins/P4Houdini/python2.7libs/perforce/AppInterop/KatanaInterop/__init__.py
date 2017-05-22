def validate():
	try:
		import Katana
	except ImportError as e:
		return False
	return True

def setup():
	import interop