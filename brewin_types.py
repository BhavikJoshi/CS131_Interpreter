from element import *


class BrewinType():
    def __init__(self):
        self.captured_by_ref = False

class BrewinNil(BrewinType):
    def __init__(self):
        super().__init__()
    def __str__(self):
        return "nil"

class BrewinBool(BrewinType):
    def __init__(self, val):
        super().__init__()
        self.value = val
    def __str__(self):
        return "true" if self.value else "false"

class BrewinFunction(BrewinType):
    def __init__(self, init_term = (None, None, None)):
        super().__init__()
        self.captured_by_ref = True
        if init_term is not (None, None, None):
            k, v, c = init_term
            self.overloads = {k: (v, c)}
    def set(self, args, func_elem, closure = None):
        self.overloads[args] = (func_elem, closure)
    def get(self, args, default = None):
        return self.overloads.get(args, default)
    def is_overloaded(self):
        return True if len(self.overloads) > 1 else False

class BrewinObject(BrewinType):

    NIL = BrewinNil()

    def __init__(self):
        super().__init__()
        self.captured_by_ref = True
        self.members = {}
        self.proto = BrewinObject.NIL

    def get_member(self, mem):
        if mem == "proto":
            if self.proto is BrewinObject.NIL:
                return None
            return self.proto
        elif mem in self.members:
            return self.members[mem]
        elif not isinstance(self.proto, BrewinNil):
            return self.proto.get_member(mem)
        return None

    def set_member(self, mem, data):
        # If the member name is proto: set the proto
        if mem == "proto":
            self.proto = data
        # Otherwise, set locally (will shadow proto)
        else:
            self.members[mem] = data