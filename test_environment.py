import sys
spacer = "======================"

print("ENVIRONMENT IS: ", sys.prefix)

print(spacer)
print("INSTALLED PACKAGES: ")
import pkg_resources
installed_packages = pkg_resources.working_set
installed_packages_list = sorted(["%s==%s" % (i.key, i.version)
    for i in installed_packages])
for m in installed_packages_list:
    print(m)
print(spacer)