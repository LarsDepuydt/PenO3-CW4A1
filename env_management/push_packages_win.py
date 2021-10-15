import os, subprocess
PATH = str(os.path.dirname(os.path.realpath(__file__))) + "\\push_packages_windows.bat"
subprocess.call(PATH)
