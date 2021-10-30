from imutils.video import VideoStream
from picamera import PiCamera
import imagezmq
import cv2
import numpy as np
from time import sleep

# =================
# CONSTANTS
# =================

RESOLUTION = (720, 480)
RB_IP_MAIN = 'tcp://169.254.222.67:5555'
RB_IP_HELPER = 'tcp://169.254.165.116:5555'


# =================
# INITIALIZATION
# =================
IMAGE_HUB = imagezmq.ImageHub()
PICAM = VideoStream(usePiCamera=True, resolution=RESOLUTION).start()
sleep(2.0)  # allow camera sensor to warm up
SENDER = imagezmq.ImageSender(connect_to=RB_IP_HELPER)

# SEND READY MESSAGE
SENDER.send(np.array(["ready"]))
print("Ready message was received")

left_image = image_hub.recv_image()[1]
image_hub.send_reply(b'OK')
print("Received left calibration image")


print("END")







