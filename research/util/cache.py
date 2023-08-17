import numpy as np
import os

# Description: Cache decorator
# cache the result of a function call in a file
# if the file exists, return the cached result

def cache(filename):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if os.path.exists(filename):
                return np.load(filename)
            else:
                result = func(*args, **kwargs)
                np.save(filename, result)
                return result
        return wrapper
    return decorator
