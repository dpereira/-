from sys import path
path += ['.']
from mayhem import scan_project, scan_modules, monitor_module, release_observers
from mayhem.zmq_pusher import setup_channel
from time import sleep
from functools import lru_cache

channel, sink = setup_channel()

module_info = {}
graph = {}
under_update = set()

@lru_cache(maxsize = len(graph))
def scan_outdated(module):
  dirty = set(graph[module]) if module in graph else set()
  needs_rebuild = set()
  while dirty:
    needs_rebuild.update(dirty)
    new_dirty = set()
    for m in dirty:
      if m in graph:
        new_dirty.update(graph[m])
    dirty = new_dirty
  return sorted(needs_rebuild, key = dependency_level, reverse = True)

@lru_cache(maxsize = len(graph))
def dependency_level(m):
  return 1 + max([dependency_level(d) for d in graph[m]]) if m in graph else 0

def rebuild(module, event, handler):
    print("Pushing %s ... " % (module,),)
    channel.send_json({"id": module['module_id'], "module": module})
    under_update.add(module['module_id'])
    print("Pushed.")

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
      read_sink()
    except Exception as e:
      release_observers()
      raise

def read_sink():
  """
  Handles worker update messages that are sent
  to the sink
  """
  message = sink.recv_json()

  print("READ SINK: received:\n%s" % (message,))

  if "module" not in message:
    print("READ SINK: spurious message received, discarding")
    return

  m = message['module']
  id = m['module_id']
  under_update.remove(id)
  dependents = sorted(graph[id] if id in graph else [] , key = dependency_level, reverse = True)
  indirect_dependents = set()

  for uu in under_update:
    indirect_dependents.update(scan_outdated(uu))

  for d in dependents:
    indirect_dependents.update(scan_outdated(d))
    if d in indirect_dependents:
      continue
    else:
      module = dict(module_info[d])
      module['module_id'] = d
      rebuild(module, None, None)


module_info, graph = scan("./external/takari-experiments/j2ee-simple", rebuild)

print("Dependency relationships are:")
for k,v in graph.items():
  print("%s <- %s" % (k , v))

wait()


