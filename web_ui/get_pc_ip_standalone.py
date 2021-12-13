from os import system
#PC_IP = system("for /f \"tokens=3 delims=: \" %i  in ('netsh interface ip show config name^=\"Ethernet\" ^| findstr \"IP Address\"') do echo Your IP Address is: %i")
#PC_IP = system("for /f \"tokens=3 delims=: \" %i  in ('netsh interface ip show config name^=\"Ethernet\" ^| findstr \"IP Address\"') return %1")

# T = system("'netsh interface ip show config name^=\"Ethernet\" ^| findstr \"IP Address\"'")

import subprocess
out = str(subprocess.run("for /f \"tokens=3 delims=: \" %i  in ('netsh interface ip show config name^=\"Ethernet\" ^| findstr \"IP Address\"') do echo %i", shell=True, capture_output=True).stdout)
i1 = out.find("echo") + 5 # deletes "echo " 
i2 = i1 + out[i1:].find("\\r") - 1 # deletes " "
PC_IP = out[i1:i2]

