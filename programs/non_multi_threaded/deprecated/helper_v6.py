import numpy as np
import cv2
import imagezmq
from imutils.video import VideoStream
from time import sleep

# ==============================
# CONSTANTS
# ==============================

CAMERAMODE =  1 # 1 = imutils.VideoStream, 2 = cv2.VideoCapture
CALIBRATION_RESOLUTION = WIDTH, HEIGHT = (640, 480)
STREAM_RESOLUTION      = (640, 480)
RB_IP_MAIN= 'tcp://169.254.165.116:5555'
RB_IP_HELPER = 'tcp://169.254.222.67:5555'
PREVIOUS_CALIBRATION_DATA_PATH = "calibration_data.txt"


if CAMERAMODE == 1:
    PICAM = VideoStream(usePiCamera=True, resolution=CALIBRATION_RESOLUTION).start()
elif CAMERAMODE == 2:
    PICAM = cv2.VideoCapture(0)
    PICAM.set(cv2.CAP_PROP_FRAME_WIDTH, CALIBRATION_RESOLUTION[0])
    PICAM.set(cv2.CAP_PROP_FRAME_HEIGHT, CALIBRATION_RESOLUTION[1])
IMAGE_HUB = imagezmq.ImageHub()

sleep(2)  # allow camera sensor to warm up and wait to make sure helper is running


# ==============================
# INITIALISATION
# ==============================
SENDER = imagezmq.ImageSender(connect_to=RB_IP_MAIN)

if IMAGE_HUB.recv_image()[1] == np.array(['ready']):
    IMAGE_HUB.send_reply(b'OK')
    print("Ready message received")

imgL = cv2.cvtColor(PICAM.read(), cv2.COLOR_BGR2BGRA)
SENDER.send_image(RB_IP_HELPER, imgL)
print("Image sent and received by main")

MAPL1, MAPL2 = IMAGE_HUB.recv_image()[1]
IMAGE_HUB.send_reply(b'OK')
print('Received MAPL1 and MAPL2')

while True:
    SENDER.send_image(RB_IP_HELPER, cv2.remap(cv2.cvtColor(PICAM.read(), cv2.COLOR_BGR2BGRA), MAPL1, MAPL2, cv2.INTER_AREA, borderMode=cv2.BORDER_TRANSPARENT))

