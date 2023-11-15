class VarScope():
    def __init__(self, trace_output):
        self.trace_output = trace_output
        self.__vars = []
        self.__args = []
        self.__aliases = []
        self.__closures = []
    
    def push(self, is_func = False, closure = None):
        self.__vars.append({})
        if is_func == True:
            self.__args.append({})
            self.__aliases.append({})
            self.__closures.append(closure)
    
    def pop(self, is_func = False, closure = None):
        self.__vars.pop()
        if is_func == True:
            self.__args.pop()
            self.__aliases.pop()
            self.__closures.pop()

    def get(self, key, default=None):
        # Use alias instead if there is one
        key = self.__get_alias(key)
        # Check stack of arguments for the key
        for d in reversed(self.__args):
            if key in d:
                return d[key]
        # Check most recent closures for the key
        for c in reversed(self.__closures):
            if c is not None and c.get(key) is not None:
                return c.get(key)
        # Check all dicts for the key (order doesn't matter since they are unique)
        for d in reversed(self.__vars):
            if key in d:
                return d[key]
        return default

    def set(self, keyo, val):
        # Use alias instead if there is one
        key = self.__get_alias(keyo)
        # If the variable doesn't exist yet
        if self.get(key, None) is None:
            self.__vars[-1][key] = val
        # If the variable exists
        else:
            # Check in function arguments first
            for d in reversed(self.__args):
                if key in d:
                    d[key] = val
                    return
            # Then check in most recent closures
            for c in reversed(self.__closures):
                if c is not None and c.get(key) is not None:
                    c.set(key, val)
                    return
            # Then check in non-arg variables
            for d in reversed(self.__vars):
                if key in d:
                    d[key] = val
                    return
    
    def add_arg(self, key, val):
        self.__args[-1][key] = val

    def add_alias(self, ref_name, prev_name, closure):
        # If the variable we created a ref to is already an alias itself,
        #       find what it refers to
        if closure:
            self.__remove_variable_from_closure(prev_name, closure)
        prev_name = self.__get_alias(prev_name)
        if closure:
            self.__remove_variable_from_closure(prev_name, closure)
        self.__aliases[-1][ref_name] = prev_name

    def __get_alias(self, key):
        for d in reversed(self.__aliases):
            if key in d:
               return d[key]
        return key

    def __remove_variable_from_closure(self, key, closure):
        if closure is None:
            return
        if closure.get(key) is None:
            return
        else:
            for c in closure.__closures:
                self.__remove_variable_from_closure(key, c)
            for d in closure.__vars:
                if key in d:
                    del d[key]
            for d in closure.__args:
                if key in d:
                    del d[key]
