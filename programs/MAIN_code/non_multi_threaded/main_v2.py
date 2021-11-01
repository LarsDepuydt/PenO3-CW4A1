from imutils.video import VideoStream
import imagezmq
import numpy as np
from time import sleep
import os

# =================
# CONSTANTS
# =================

RESOLUTION = (720, 480)
RB_IP_MAIN = 'tcp://169.254.222.67:5555'
RB_IP_HELPER = 'tcp://169.254.165.116:5555'
PORT = 'tcp://localhost:5556'
INIT_HELPER_CMD = "sh ssh_login_and_run_file.sh 'cd Desktop/PenO3-CW4A1/programs/MAIN_code/non_multi_threaded;python3 ./test_helper.py'"

# =================
# INITIALIZATION
# =================
os.system(INIT_HELPER_CMD)       # init helper pi
IMAGE_HUB = imagezmq.ImageHub()
PICAM = VideoStream(usePiCamera=True, resolution=RESOLUTION).start()
sleep(3.0)  # allow camera sensor to warm up and wait to make sure helper is running
SENDER = imagezmq.ImageSender(connect_to=RB_IP_HELPER)

# SEND READY MESSAGE
SENDER.send_image(RB_IP_MAIN, np.array(["ready"]))
print("Ready message was received")

left_image = IMAGE_HUB.recv_image()[1]
IMAGE_HUB.send_reply(b'OK')
print("Received left calibration image")


print("test_main.py END")







