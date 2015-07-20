from sys import path
path += ['.']
from mayhem import scan_project, scan_modules, monitor_module, release_observers
from time import sleep
from functools import lru_cache

module_info = {}
graph = {}

def scan_outdated(module, event, handler):
  print("Calculating rebuild for change triggered in %s:\n%s" % (module['module_id'], event))
  dirty = set([module['module_id']])
  needs_rebuild = set()
  while dirty:
    needs_rebuild.update(dirty)
    new_dirty = set()
    for m in dirty:
      try:
          new_dirty.update(graph[m])
      except KeyError:
        pass
    dirty = new_dirty
  print("Modules to be rebuilt:\n%s" % needs_rebuild)
  return sorted(needs_rebuild, key = dependency_level, reverse = True)

@lru_cache(maxsize = len(graph))
def dependency_level(m):
  return 1 + max([dependency_level(d) for d in graph[m]]) if m in graph else 0

def rebuild(module, event, handler):
  for m in scan_outdated(module, event, handler):
    if module_info[m]['packaging'] != 'pom':
      print("REBUILDING %s (%s)" % (m, module_info[m]['packaging']))
    else:
      print("SKIPPING %s (%s)" % (m, module_info[m]['packaging']))

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


