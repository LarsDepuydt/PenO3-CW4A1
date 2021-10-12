import sys
spacer = "======================"

print("CURRENT PYTHON VERSION: ", sys.version)
print("GLOBAL PYTHON INSTALL : ", sys.base_prefix)
print("ACTIVE ENVIRONMENT IS : ", sys.prefix)

print(spacer)
print("INSTALLED PACKAGES: ", "\n")
import pkg_resources
installed_packages = pkg_resources.working_set
installed_packages_list = sorted(["%s==%s" % (i.key, i.version)
    for i in installed_packages])
for m in installed_packages_list:
    print(m)

print(spacer)