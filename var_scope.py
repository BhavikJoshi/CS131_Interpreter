class VarScope():
    def __init__(self):
        self.__vars = []
        self.__args = []
    
    def push(self, is_func = False):
        self.__vars.append({})
        if is_func == True:
            self.__args.append({})
    
    def pop(self, is_func = False):
        self.__vars.pop()
        if is_func == True:
            self.__args.pop()

    def get(self, key, default=None):
        # Check stack of arguments for the key
        for d in reversed(self.__args):
            if key in d:
                return d[key]
        # Check all dicts for the key (order doesn't matter since they are unique)
        for d in reversed(self.__vars):
            if key in d:
                return d[key]
        return default

    def set(self, key, val):
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
            # Then check in non-arg variables
            for d in reversed(self.__vars):
                if key in d:
                    d[key] = val
                    return
    
    def add_arg(self, key, val):
        self.__args[-1][key] = val