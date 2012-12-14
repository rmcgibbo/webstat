import zmq
import sys
sys.path.append('/home/rmcgibbo/webstat')
from webstat import settings
ctx = zmq.Context()

for daemon in settings.daemons:
    sock = ctx.socket(zmq.REQ)
    sock.connect('tcp://%s:%d' % (daemon['host'], daemon['port']))
    sock.send('hello')

    print 'Recieving on %s' % daemon
    print sock.recv()[0:100]
