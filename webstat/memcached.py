import pylibmc
import functools
import hashlib

import settings

client = pylibmc.Client(['127.0.0.1'], binary=True,
            behaviors={"tcp_nodelay": True, "ketama": True})

__all__ = ['memcached', 'flush_all']

def flush_all():
    client.flush_all()

def memcached(f):
    # from http://www.zieglergasse.at/blog/2011/python/memcached-decorator-for-python/

    @functools.wraps(f)
    def newfn(*args, **kwargs):
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
            print 'Hit memcache'
            return value

        print 'Hitting DB'
        value = f(*args, **kwargs)
        client.set(key, value, settings.memcache_residence_time)
        return value

    return newfn