import os
import re
import sys
import time
import subprocess  
import lxml, lxml.etree
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
  scanned = []

  for m in module_paths:
    try: 
      scanned.append(scan_module(m))
    except ValueError:
      continue

  return _extract_module_info(scanned)

def scan_module(module_path):
  try:
    pom = open(module_path, 'r')
    xml = etree.XML(pom.read().encode())
    objectify.deannotate(xml, cleanup_namespaces = True)
    pom.close()

    m = dict(xml.nsmap)
    namespace_prefix = ''
    if None in m:
      namespace_prefix = 'd:'
      m['d'] = m[None]
      del m[None]

    # extracts from a pom xml tree  
    # the data of interest
    ex = lambda e: (
      # module id
      e.findtext("%sgroupId" % namespace_prefix, namespaces = m) or 
      e.findtext("%sparent/%sgroupId" % (namespace_prefix, namespace_prefix), namespaces = m), 
      e.findtext("%sartifactId" % namespace_prefix, namespaces = m), 
      # module type
      e.findtext("%spackaging" % namespace_prefix, namespaces = m),
      # dependencies
      list(ex(d) for d in e.xpath("%sdependencies/*" % namespace_prefix, namespaces = m)) + 
      list(ex(p) for p in e.xpath("%sparent" % namespace_prefix, namespaces = m))
    )

    group, artifact, packaging, dependencies = ex(xml)

    return group, artifact, packaging, dependencies, os.path.dirname(module_path)
  except lxml.etree.XMLSyntaxError:
    print("WARNING: %s failed to be parsed, this project will be ignored" % module_path)
    raise ValueError("%s does not have a valid POM file" % module_path)

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
