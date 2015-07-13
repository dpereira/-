import os
import re
import sys
import subprocess

_default_project_file_patterns = ('^pom.xml$',)
_default_project_file_matchers = tuple((re.compile(p) for p in _default_project_file_patterns))

def scan_project(project_path):
  project_files = set()
  for path, directories, files in os.walk(project_path, followlinks = True):
    matching_files = filter(lambda f: tuple((m for m in _default_project_file_matchers if m.match(f))), files)
    project_files.update((os.path.join(path, f) for f in matching_files))
    
    #print(path, directories, files, tuple(matching_files))

  return project_files

def scan_modules(module_paths):
  return [scan_module(m) for m in module_paths]

def scan_module(module_path):
  subprocess.call(("mvn", "dependency:tree", "-f", module_path))
	
