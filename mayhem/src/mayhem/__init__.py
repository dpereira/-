import os
import re
import sys
import time
import subprocess
from lxml import etree, objectify
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

_default_project_file_patterns = ('^pom.xml$',)
_default_project_file_matchers = tuple((re.compile(p) for p in _default_project_file_patterns))

def scan_project(project_path):
  project_files = set()
  for path, directories, files in os.walk(project_path, followlinks = True):
    matching_files = filter(lambda f: tuple((m for m in _default_project_file_matchers if m.match(f))), files)
    project_files.update((os.path.join(path, f) for f in matching_files))
    
  return sorted(project_files, key = lambda i: len(i), reverse = True)

def scan_modules(module_paths):
  return _build_graph([scan_module(m) for m in module_paths])

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

def _build_graph(data):
  """
  Returns a data structure better
  suited to represent the graph 
  structure of the data.

  """
  return dict(
    (
      ("%s.%s" % (group, artifact)), 
      {  
        'packaging': packaging, 
        'dependencies': tuple(("%s.%s" % (dgroup, dartifact)) for dgroup, dartifact, dpkg, ddeps in dependencies),
        'path': dirname
      }
    )
    for group, artifact, packaging, dependencies, dirname in data
  )

def monitor_graph(depependency_graph):
    pass

_observers = []

class _ModuleEventHandler(FileSystemEventHandler):
    def on_any_event(event):
        print("RX: %s" % event)

def monitor_module(module_id, module_info, callback):
   print("Monitoring %s" % module_info['path'])
   observer = Observer()
   observer.schedule(_ModuleEventHandler(), module_info['path'], recursive = True)
   observer.start()
   _observers.append(observer)


def release_observers():
    for o in _observers:
        o.stop()
    for o in _observers:
        o.join()
