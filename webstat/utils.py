from subprocess import Popen, PIPE
import shlex
import functools
from datetime import datetime
import time  # unix time
import pytz

__all__ = ['coffeefactory', 'maxfrequency']


def maxfrequency(timeout):
    "Decorator to prevent a function from being called too frequently"
    def _maxfrequency(f):
        # because of the lack of nonlocal in python2.x, we need to put
        # last_time in a mutable container
        # http://stackoverflow.com/questions/1261875/python-nonlocal-statement
        last_time = [None]
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            now = time.time()
            if last_time[0] is None or (now - last_time[0]) > timeout:
                last_time[0] = now
                return f(*args, **kwargs)
            return False
            
        return wrapper
    return _maxfrequency
