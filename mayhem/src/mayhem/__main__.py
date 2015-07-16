from sys import path
path += ['.']
from mayhem import scan_project, scan_modules, monitor_module, release_observers
from time import sleep

def test(path):
  pom_list = scan_project(path)
  dependency_graph = scan_modules(pom_list)

  print("SUMMARY\n")
  print("List of pom files scanned:")
  print('\n'.join(pom_list))
  print("Dependency relationships scanned:\n")

  for k, v in dependency_graph.items():
    print("%s:" % k)
    for k2, v2 in v.items():
      print("\t%s: %s" % (k2, v2))

    monitor_module(k, v, None)

  while True:
      try:
          sleep(1)
      except:
          release_observers()

#test("./external/takari-experiments/j2ee-simple-takari")
test("./external/takari-experiments/j2ee-simple")


