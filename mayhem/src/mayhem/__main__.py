from sys import path
path += ['.']
from mayhem import scan_project, scan_modules, monitor_module, release_observers
from mayhem.zmq_pusher import setup_channel
from time import sleep
from functools import lru_cache

channel = setup_channel()

module_info = {}
graph = {}

def scan_outdated(module, event, handler):
  dirty = set([module['module_id']])
  needs_rebuild = set()
  while dirty:
    needs_rebuild.update(dirty)
    new_dirty = set()
    for m in dirty:
      try:
          new_dirty.update(graph[m])
      except KeyError as e:
        print("KERR: %s" % e)
        pass
    dirty = new_dirty
  return sorted(needs_rebuild, key = dependency_level, reverse = True)

@lru_cache(maxsize = len(graph))
def dependency_level(m):
  return 1 + max([dependency_level(d) for d in graph[m]]) if m in graph else 0

def rebuild(module, event, handler):
  for m in scan_outdated(module, event, handler):
    print("GOT CHANGE:\n\t -> %s" % (module,))
    channel.send_json({"module": m})
#  cmd = ""
#  for m in scan_outdated(module, event, handler):
#    if module_info[m]['packaging'] != 'pom':
#      cmd += run_mvn_cmd(m, module_info[m]) + "; "
#  print(cmd)

def run_mvn_cmd(id, module, goals = ['install']):
  return "; ".join('mvn -f %s/pom.xml %s' % (module['path'], g) for g in goals)


def scan(path, callback):
  pom_list = scan_project(path)
  module_info, dependency_graph = scan_modules(pom_list)

  for k, v in module_info.items():
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

module_info, graph = scan("./external/takari-experiments/maven", rebuild)

print("Dependency relationships are:")
for k,v in graph.items():
  print("%s <- %s" % (k , v))

wait()


