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
SENDER = imagezmq.ImageSender(connect_to=RB_IP_MAIN)

# WAIT FOR READY MESSAGE
ready_message = image_hub.recv_image()[1]
assert ready_message == np.array(["ready"])
print("Received ready message")
image_hub.send_reply(b'OK')


# TAKE AND SEND LEFT CALIBRATION IMAGE
sender.send_image(RB_IP_HELPER, PICAM.read())
print("Left calibration image sent.")




print("END")



