from imutils.video import VideoStream
import imagezmq
import numpy as np
from time import sleep

# =================
# CONSTANTS
# =================

RESOLUTION = (720, 480)
RB_IP_MAIN = 'tcp://mainraspberry:5555'
RB_IP_HELPER = 'tcp://helperraspberry:5555'


# =================
# INITIALIZATION
# =================
IMAGE_HUB = imagezmq.ImageHub()
PICAM = VideoStream(usePiCamera=True, resolution=RESOLUTION).start()
sleep(2.0)  # allow camera sensor to warm up
SENDER = imagezmq.ImageSender(connect_to=RB_IP_HELPER)

# SEND READY MESSAGE
SENDER.send_image(RB_IP_MAIN, np.array(["ready"]))
print("Ready message was received")

left_image = IMAGE_HUB.recv_image()[1]
image_hub.send_reply(b'OK')
print("Received left calibration image")


print("END")







