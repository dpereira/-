import os
import re
import sys
import time
import subprocess  
from lxml import etree, objectify
from watchdog.events import RegexMatchingEventHandler
from watchdog.observers.polling import PollingObserver

_default_project_file_patterns = ('^pom.xml$',)
_default_project_file_matchers = tuple((re.compile(p) for p in _default_project_file_patterns))

def scan_project(project_path):
  project_files = set()
  for path, directories, files in os.walk(project_path, followlinks = True):
    matching_files = filter(lambda f: tuple((m for m in _default_project_file_matchers if m.match(f))), files)
    project_files.update((os.path.join(path, f) for f in matching_files))
    
  return sorted(project_files, key = lambda i: len(i), reverse = True)

def scan_modules(module_paths):
  return _extract_module_info([scan_module(m) for m in module_paths])

def scan_module(module_path):
  pom = open(module_path, 'r')
  xml = etree.XML(pom.read().encode())
  objectify.deannotate(xml, cleanup_namespaces = True)
  pom.close()

  m = dict(xml.nsmap)
  m['d'] = m[None]
  del m[None]

  # extracts from a pom xml tree  
  # the data of interest
  ex = lambda e: (
    # module id
    e.findtext("d:groupId", namespaces = m), 
    e.findtext("d:artifactId", namespaces = m), 
    # module type
    e.findtext("d:packaging", namespaces = m),
    # dependencies
    list(ex(d) for d in e.xpath("d:dependencies/*", namespaces = m)) + 
    list(ex(p) for p in e.xpath("d:parent", namespaces = m))
  )

  group, artifact, packaging, dependencies = ex(xml)

  return group, artifact, packaging, dependencies, os.path.dirname(module_path)

def _extract_module_info(data):
  """
  Returns a data structure better
  suited to represent the graph 
  structure of the data.

  """
  graph = {}
  module_id = lambda group, artifact: "%s.%s" % (group, artifact)

  for group, artifact, packaging, dependencies, dirname in data:
    id = module_id(group, artifact)
    for dgroup, dartifact, unused, unused2 in dependencies:
      dependency_id = module_id(dgroup, dartifact)
      try:
        graph[dependency_id].append(id)
      except (KeyError, TypeError):
        graph[dependency_id] = [id]

  return dict(
    (
      module_id(group, artifact), 
      {  
        'packaging': packaging, 
        'dependencies': tuple((module_id(dgroup, dartifact)) for dgroup, dartifact, dpkg, ddeps in dependencies),
        'path': dirname
      }
    )
    for group, artifact, packaging, dependencies, dirname in data
  ), graph

def monitor_graph(depependency_graph):
    pass

_observers = []
_observable_fs_objects = [ ('', False), ('src', True)]
_include_regexes = ['.*\.java', '.*pom\.xml']
_exclude_regexes = []

class _ModuleEventHandler(RegexMatchingEventHandler):

  def __init__(self, module_id, module_info, callback):
    super().__init__(_include_regexes, _exclude_regexes)
    self._module_id = module_id
    self._module_info = module_info
    self._callback = callback
    
  def on_any_event(self, event):
    module_info = dict(self._module_info)
    module_info.update({'module_id': self._module_id})
    self._callback(module_info, event, self)

def monitor_module(module_id, module_info, callback):
  event_handler = _ModuleEventHandler(module_id, module_info, callback)

  for fs_object, recursive in _observable_fs_objects:
    observer = PollingObserver()
    observable = os.sep.join((module_info['path'], fs_object))
    if os.path.exists(observable):
      observer.schedule(event_handler, observable, recursive = recursive)
      observer.start()
      _observers.append(observer)

def release_observers():
  for o in _observers:
    o.stop()
  for o in _observers:
    o.join()
