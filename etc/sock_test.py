import zmq
ctx = zmq.Context()
sock = ctx.socket(zmq.REQ)
sock.connect('tcp://vsp-compute:76215')
sock.send_json('hello')
