from element import *

class BrewinNil():
    def __init__(self):
        pass
    def __str__(self):
        return "nil"

class BrewinBool():
    def __init__(self, val):
        self.value = val
    def __str__(self):
        return "true" if self.value else "false"

class BrewinFunction():
    def __init__(self, init_term = (None, None, None)):
        if init_term is not (None, None):
            k, v, c = init_term
            self.overloads = {k: (v, c)}
    def set(self, args, func_elem, closure = None):
        self.overloads[args] = (func_elem, closure)
    def get(self, args, default = None):
        return self.overloads.get(args, default)
    def is_overloaded(self):
        return True if len(self.overloads) > 1 else False
