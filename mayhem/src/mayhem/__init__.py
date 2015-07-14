import os
import re
import sys
import time
import subprocess
from lxml import etree, objectify

_default_project_file_patterns = ('^pom.xml$',)
_default_project_file_matchers = tuple((re.compile(p) for p in _default_project_file_patterns))

def scan_project(project_path):
  project_files = set()
  for path, directories, files in os.walk(project_path, followlinks = True):
    matching_files = filter(lambda f: tuple((m for m in _default_project_file_matchers if m.match(f))), files)
    project_files.update((os.path.join(path, f) for f in matching_files))
    
    #print(path, directories, files, tuple(matching_files))

  return sorted(project_files, key = lambda i: len(i), reverse = True)

def scan_modules(module_paths):
  return [scan_module(m) for m in module_paths]

def scan_module(module_path):
  pom = open(module_path, 'r')
  xml = etree.XML(pom.read().encode())
  objectify.deannotate(xml, cleanup_namespaces = True)
  pom.close()


  m = dict(xml.nsmap)
  m['d'] = m[None]
  del m[None]

  print(m)

  ex = lambda e: (
    e.findtext("d:groupId", namespaces = m), 
    e.findtext("d:artifactId", namespaces = m), 
    e.findtext("d:packaging", namespaces = m),
    e.xpath("d:dependencies/*", namespaces = m)
  )

  group, artifact, packaging, dependencies = ex(xml)
  dependencies = tuple(ex(d) for d in dependencies)

  print(group, artifact, packaging, dependencies)

  return extract_dependencies(dependencies)


    

#  tmp = open('/tmp/subprocess.%s' % time.time(), "x+")
#  subprocess.call(("mvn", "dependency:tree", "-f", module_path), stdout = tmp, stderr = subprocess.STDOUT)
#  tmp.seek(0)
#  contents = tmp.read()
#  tmp.close()
#  return extract_dependencies(contents)

def extract_dependencies(output):
  deployable_packages = ('war', 'ear')
  dependency_packages = ('jar','pom')

#def extract_dependencies(output):
#  dependency_prefix_pattern = '\[INFO\]\s'
#  dependency_patterns = ('\+(.*)','\|(.*)',"\\\\(.*)")
#  dependency_matchers = tuple(re.compile(dependency_prefix_pattern + pattern) for pattern in dependency_patterns)
#  dependencies = []
#  for l in output.split('\n'):
#    for matcher in dependency_matchers:
#        m = matcher.match(l)
#        if m:
#          dependencies.append(m.group(1))
#          break
#
#  return dependencies
 
