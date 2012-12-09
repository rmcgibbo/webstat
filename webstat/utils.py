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


class NonZeroExitError(Exception):
    def __init__(self, command, returncode, output, error):
        self.command = command
        self.returncode = returncode
        self.output = output
        self.error = error
    def __str__(self):
        return '''\
        %s returned non-zero exit status %d with output
        %s
        and error
        %s''' % (self.command, self.returncode,
                 self.output or "[NO OUTOUT]",
                 self.error or "[NO ERROR]")

def command_line_renderer_factory(command):
    '''command should be a command reads input from stdin
    and prints to stdout'''
    
    args = shlex.split(command)
    
    def renderer(script):
        '''Accepts a file object or path and return the
        rendered string'''
        
        if isinstance(script, file):
            pass
        elif isinstance(script, str):
            script = open(script)
        else:
            raise TypeError('script must be a file object of '
                            'or a string to the file')
        process = Popen(args, stdin=script,
                        stdout=PIPE, stderr=PIPE)
        
        returncode = process.wait()
        stdoutdata, stderrdata = process.communicate()
        
        if returncode != 0:
            raise NonZeroExitError(command, returncode,
                                   stdoutdata, stderrdata)
        process.wait()
        return stdoutdata
    
    return renderer

coffeefactory = command_line_renderer_factory('coffee -cs')