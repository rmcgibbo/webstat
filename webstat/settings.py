import os
import pytz
ROOT = os.path.abspath(os.path.dirname(__file__))

timezone = pytz.timezone('US/Pacific')

# the hostname (or ip) and ip for the daemons, to conntect to over ZMQ
daemons = [{'host': 'vsp-compute', 'port': 7621,
            'name': 'vsp-compute', 'id': 1, 'default': True},
           {'host': 'vspm10', 'port': 7620,
            'name': 'certainty', 'id': 2, 'default': False},
           ]

# Rough time that computed queries stay in the memcache
# before going stale
# This value can be HIGH, since when the webserver recieves
# new data from the daemons, it automatically flushes the
# memcachce
memcache_residence_time = 5*60 # seconds

# this is the maximum frequency (minimum period)
# that we poll the daemons at. When clients ask
# more frequently, we tell them no.
daemon_poll_min_period  = 30 # seconds
daemon_poll_default_period_minutes = 20

zmq_auth_keys = 'none'

public_path = os.path.join(ROOT, 'public')
