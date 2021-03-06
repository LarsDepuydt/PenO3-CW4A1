import sys, os
spacer = "======================"

print("CURRENT PYTHON VERSION      : ", sys.version)
print("GLOBAL PYTHON INSTALL       : ", sys.base_prefix)
print("ACTIVE ENVIRONMENT IS       : ", sys.prefix)
print("ACTIVE ENVIRONMENT SHOULD BE: ", str(os.path.dirname(os.path.realpath(__file__)))[:-15]+ "\\venv")

print(spacer)
print("INSTALLED PACKAGES: ", "\n")
import pkg_resources
installed_packages = pkg_resources.working_set
installed_packages_list = sorted(["%s==%s" % (i.key, i.version)
    for i in installed_packages])
for m in installed_packages_list:
    print(m)
print(spacer)
print('List may be wrong, run \n cd venv/Scripts \n pip list -l \n to get a definitive list of local packages')
print(spacer)