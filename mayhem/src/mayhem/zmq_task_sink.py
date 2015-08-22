"""
This streamer is used to
distribute load from the 
zmq_pushers to the zmq_pullers.
Within mayhem, pushers notify of
changes in project code or configuration,
while pullers consume these notifications
and then perform the build operations using maven
that are required to update the code.

"""
import zmq

def main():
  context = zmq.Context(1)
  frontend = context.socket(zmq.PULL)
  frontend.bind("tcp://*:66602")
  backend = context.socket(zmq.PUSH)
  backend.bind("tcp://*:66603")

  try:
    zmq.device(zmq.STREAMER, frontend, backend)
  except Exception as e:
    print("Device down:\n%s" % (e,))
  finally:
    frontend.close()
    backend.close()
    context.term()

if __name__ == "__main__":
  main()
