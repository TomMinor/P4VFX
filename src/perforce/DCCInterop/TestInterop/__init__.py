import inspect

def in_unittest():
    # http://stackoverflow.com/questions/25025928/how-can-a-piece-of-python-code-tell-if-its-running-under-unittest
    current_stack = inspect.stack()
    for stack_frame in current_stack:
        # This element of the stack frame contains
        for program_line in stack_frame[4]:
            if "unittest" in program_line:       # some contextual program lines
                return True
    return False

def validate():
	return in_unittest()

def setup():
	import interop