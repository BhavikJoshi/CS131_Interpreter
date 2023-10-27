class VarScope():
    def __init__(self):
        self.__vars = []
    
    def push(self):
        self.__vars.append({})
    
    def pop(self):
        self.__vars.pop()

    def get(self, key, default=None):
        # Check all dicts for the key
        for d in self.__vars:
            if key in d:
                return d[key]
        return default

    def set(self, key, val):
        # If the variable doesn't exist yet
        if self.get(key, None) is None:
            self.__vars[-1][key] = val
        # If the variable exists
        else:
            for d in self.__vars:
                if key in d:
                    d[key] = val