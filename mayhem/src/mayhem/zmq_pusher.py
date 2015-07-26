"""
This module pushes events 
to whoever pullers are listening.

"""

import zmq

def setup_channel():
  context = zmq.Context()
  zmq_socket = context.socket(zmq.PUSH)
  zmq_socket.bind("tcp://0.0.0.0:66601")
  return zmq_socket


