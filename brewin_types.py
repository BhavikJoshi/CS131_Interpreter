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
    def __init__(self, func_elem):
        self.elem = func_elem
