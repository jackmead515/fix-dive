import time
import logging

def profile_time(name):
    def inner(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            elapsed = end - start
            logging.info(f'{name} took {elapsed} seconds')

            return result
        return wrapper
    return inner