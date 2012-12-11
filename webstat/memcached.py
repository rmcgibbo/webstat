import pylibmc
import functools
import hashlib

import settings

client = pylibmc.Client(['127.0.0.1'], binary=True,
            behaviors={"tcp_nodelay": True, "ketama": True})

__all__ = ['memcached', 'flush_all']

def flush_all():
    client.flush_all()

def memcached(*args, **kwargs):
    """memcached decorator
    
    Call either as

    # the timeout will be the default one from settings.memcache_residence_time
    >>> @memcached  
    >>> def f(x):
    ...    pass
    
    or 
    
    >>> @memached(timeout=1)  # or set the timeout yourself
    >>> def f(x):
    ...    pass
    
    """
    
    #http://stackoverflow.com/questions/3931627/how-to-build-a-python-decorator-with-optional-parameters/3931903#3931903
    # from http://www.zieglergasse.at/blog/2011/python/memcached-decorator-for-python/

    def _memcached(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # generate md5 out of args and function
            m = hashlib.md5()
            margs = [x.__repr__() for x in args]
            mkwargs = [x.__repr__() for x in kwargs.values()]
            map(m.update, margs + mkwargs)
            m.update(f.__name__)
            m.update(f.__class__.__name__)
            key = m.hexdigest()

            value = client.get(key)
            if value is not None:
                #print 'HIT memcache on %s' % f.__name__
                return value

            #print 'PASS memcache (went to db) on %s' % f.__name__
            value = f(*args, **kwargs)
            client.set(key, value, settings.memcache_residence_time)
            return value

        return wrapper

    if len(args) == 1 and callable(args[0]):
        # No arguments, this is the decorator
        # Set default values for the arguments
        timeout = settings.memcache_residence_time
        return _memcached(args[0])

    else:
        # This is just returning the decorator
        timeout = kwargs.pop('timeout', settings.memcache_residence_time)
        return _memcached