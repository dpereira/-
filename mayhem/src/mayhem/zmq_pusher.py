"""
This module pushes events 
to whoever pullers are listening.

"""

import zmq

def setup_channel():
  context = zmq.Context()
  zmq_socket = context.socket(zmq.PUSH)
  zmq_socket.connect("tcp://127.0.0.1:66600")
  return zmq_socket


