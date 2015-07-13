from sys import path
path += ['.']
from mayhem import scan_project, scan_module

pom_list = scan_project(".")
dependency_tree = [(p, scan_module(p)) for p in pom_list]

print("SUMMARY\n")
print("List of pom files scanned:")
print('\n'.join(pom_list))
print("Dependency relationships scanned:\n")
(print(p, d) for p, d in dependency_tree)
