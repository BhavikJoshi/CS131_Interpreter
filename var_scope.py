class VarScope():
    def __init__(self):
        self.__vars = []
        self.__args = []
        self.__aliases = []
    
    def push(self, is_func = False):
        self.__vars.append({})
        if is_func == True:
            self.__args.append({})
            self.__aliases.append({})
    
    def pop(self, is_func = False):
        self.__vars.pop()
        if is_func == True:
            self.__args.pop()
            self.__aliases.pop()

    def get(self, key, default=None):
        # Use alias instead if there is one
        key = self.__get_alias(key)
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
        # Use alias instead if there is one
        key = self.__get_alias(key)
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

    def add_alias(self, ref_name, prev_name):
        # If the variable we created a ref to is already an alias itself,
        #       find what it refers to
        prev_name = self.__get_alias(prev_name)
        self.__aliases[-1][ref_name] = prev_name


    def __get_alias(self, key):
        for d in reversed(self.__aliases):
            if key in d:
               return d[key]
        return key