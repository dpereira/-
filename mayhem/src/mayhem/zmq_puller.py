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
  frontend.connect("tcp://127.0.0.1:66601")

  try:
    while True:
      work = frontend.recv_json()
      print(" -> GOT: %s", (work,))
  except Exception as e:
    print("Puller down:\n%s" % (e,))
  finally:
    frontend.close()
    context.term()

if __name__ == "__main__":
  main()
