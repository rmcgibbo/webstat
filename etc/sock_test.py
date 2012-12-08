import zmq
ctx = zmq.Context()
sock = ctx.socket(zmq.REQ)
sock.bind('tcp://127.0.0.1:76215')
sock.send_json('hello')
