import os
PROG_DIR =  str(str(os.path.dirname(os.path.realpath(__file__)))[:-37] + "programs/MAIN_code/non_multi_threaded").replace("\\", "/")
REMOTE_EXEC_SCRIPT_PATH = PROG_DIR + "/ssh_conn_and_execute_cmd_win.bat"
print(REMOTE_EXEC_SCRIPT_PATH)
MAIN_CMD_FILE = PROG_DIR + "/main_terminate.txt"
HELPER_CMD_FILE = PROG_DIR + "/helper_terminate.txt"
import subprocess
subprocess.run([REMOTE_EXEC_SCRIPT_PATH, "169.254.222.67", MAIN_CMD_FILE])
subprocess.run([REMOTE_EXEC_SCRIPT_PATH, "169.254.165.116", HELPER_CMD_FILE])