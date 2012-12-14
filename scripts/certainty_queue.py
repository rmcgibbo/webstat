"""
This is a ZeroMQ device that forwards messages to certainty

It sits on a computer with SSH access to certainty and accepts
connections on port 7620 which get forwarded to certainty-b
on port 7621 over SSH
"""

import os
import daemon
import lockfile

def main():
    # put the imports in here, because ssh opens a file descriptor (/dev/urandom I think)
    # which gets broken if you do it before daemonizing
    import zmq
    from zmq import ssh

    try:
        context = zmq.Context(1)
        # Socket facing clients

        frontend = context.socket(zmq.XREP)
        frontend.bind("tcp://*:7620")
        # Socket facing services

        backend = context.socket(zmq.XREQ)
        ssh.tunnel_connection(backend, 'tcp://127.0.0.1:7621', 'certainty-b')

        zmq.device(zmq.QUEUE, frontend, backend)
    except Exception, e:
        print e
        print "bringing down zmq device"
    finally:
        pass
        frontend.close()
        backend.close()
        context.term()

if __name__ == "__main__":
    log = open('certainty_queue.log', 'a+')
    lock = lockfile.FileLock(os.path.expanduser('~/.certainty_queue.pid'))
    if lock.is_locked():
        raise RuntimeError('Already Running')
    with daemon.DaemonContext(pidfile=lock, stdout=log, stderr=log):
        main()
