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
import zmq, os, subprocess

def main():
  context = zmq.Context(1)
  frontend = context.socket(zmq.PULL)
  frontend.connect("tcp://127.0.0.1:66601")

  sink = context.socket(zmq.PUSH)
  sink.connect("tcp://127.0.0.1:66602")

  try:
    while True:
      # receive
      outdated_module = frontend.recv_json()

      # work
      print("-> %s" % (outdated_module,))
      current = os.getcwd()
      os.chdir(outdated_module['module']['path'])
      try:
        subprocess.check_call(("mvn","install"))
      except subprocess.CalledProcessError as e:
        print("Puller %s failing with %s" % (context.underlying, e))
      os.chdir(current)

      # notify done
      sink.send_json(outdated_module)
  except Exception as e:
    print("Puller %s down:\n%s" % (context.underlying, e))
  finally:
    frontend.close()
    context.term()

if __name__ == "__main__":
  main()
