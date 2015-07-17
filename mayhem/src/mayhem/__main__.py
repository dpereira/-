from sys import path
path += ['.']
from mayhem import scan_project, scan_modules, monitor_module, release_observers
from time import sleep

module_info = {}
graph = {}

def rebuild(module, event, handler):
  print("Calculating rebuild for change triggered in %s:\n%s" % (module['module_id'], event))
  module_id = module['module_id']
  dirty = set([module_id])
  needs_rebuild = set()
  while dirty:
    needs_rebuild.update(dirty)
    new_dirty = set()
    for module in dirty:
      try:
        new_dirty.update(set(graph[module]))
      except KeyError:
        pass
    dirty = new_dirty
  print("Modules to be rebuilt:\n%s" % needs_rebuild)

def scan(path, callback):
  pom_list = scan_project(path)
  module_info, dependency_graph = scan_modules(pom_list)

  print("SUMMARY\n")
  print("List of pom files scanned:")
  print('\n'.join(pom_list))
  print("Dependency relationships scanned:\n")

  for k, v in module_info.items():
    print("%s:" % k)
    for k2, v2 in v.items():
      print("\t%s: %s" % (k2, v2))

    monitor_module(k, v, callback)

  return module_info, dependency_graph

def wait():
  while True:
    try:
      sleep(1)
    except:
      print("Monitoring loop broken")
      release_observers()
      break

#scan("./external/takari-experiments/j2ee-simple-takari")
module_info, graph = scan("./external/takari-experiments/j2ee-simple", rebuild)
print("-->%s", graph)
wait()


