import os
from time import sleep
KILL_HELPER_PYTHON_CMD = "sh ssh_conn_and_execute_cmd.sh 'sudo netstat -ltnp; pkill -f helper_v2.py; sudo netstat ltnp'"

sleep(5)

os.system(KILL_HELPER_PYTHON_CMD)       # init helper pi

KILL_HELPER_PYTHON_CMD = "sh ssh_conn_and_execute_cmd.sh 'sudo netstat -ltnp; pkill -f /usr/bin/python3.py; sudo netstat ltnp'"
os.system(KILL_HELPER_PYTHON_CMD)  