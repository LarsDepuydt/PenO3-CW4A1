print("HELPER V9 INITIALIZED")
import numpy as np
from sys import argv
import cv2
import imagezmq
from imutils.video import VideoStream
from time import sleep


# ==============================
# ARGUMENT PARSER
# ==============================

# args = "True" "width,height" "blend_frac" "x_t" "pc_ip"
if len(argv) > 1:
    USE_KEYPOINT_TRANSLATE = bool(int(argv[1]))
    RESOLUTION = WIDTH, HEIGHT = [int(x) for x in argv[2].split(",")]
    BLEND_FRAC = float(argv[3])
    X_TRANS_DIST = int(argv[4])
    PC_IP = "tcp://" + argv[5] + ":5555"
else:
    USE_KEYPOINT_TRANSLATE = False
    RESOLUTION = WIDTH, HEIGHT = [320, 240]
    BLEND_FRAC = 0.5
    X_TRANS_DIST = 28
    PC_IP = "tcp://" + "169.254.236.78" + ":5555"

# ==============================
# CONSTANTS
# ==============================

FOCAL_LEN = 210 # focal length = 3.15mm volgens waveshare.com/imx219-d160.htm
s = 0 # skew parameter
KL = np.array([[FOCAL_LEN, s, WIDTH/2], [0, FOCAL_LEN, HEIGHT/2], [0, 0, 1]], dtype=np.uint16)  # mock intrinsics
KR = np.array([[FOCAL_LEN, 0, WIDTH/2], [0, FOCAL_LEN, HEIGHT/2], [0, 0, 1]], dtype=np.uint16)  # mock intrinsics
# [fx s x0; 0 fy y0; 0 0 1]

PICAM = VideoStream(usePiCamera=True, resolution=RESOLUTION).start()

IMAGE_HUB = imagezmq.ImageHub()
print("here")
RB_IP_MAIN, ready = IMAGE_HUB.recv_image()
if ready[0] == "ready":
    print("Received ready message")
IMAGE_HUB.send_reply(b'OK') # main continues after this and also takes picture
sleep(1)  # allow camera sensor to warm up and wait to make sure helper is running
SENDER = imagezmq.ImageSender(connect_to=RB_IP_MAIN)

# ==============================
# INITIALISATION
# ==============================
print("here")

imgL = cv2.cvtColor(PICAM.read(), cv2.COLOR_BGR2BGRA)
SENDER.send_image("", imgL)
print("Left calibration image was received by main")

MAPLX, MAPLY = IMAGE_HUB.recv_image()[1]
IMAGE_HUB.send_reply(b'OK')
print("Received MAPLX and MAPLY")

# ==============================
# LOOP
# ==============================

while True:
    SENDER.send_image("", cv2.remap(cv2.cvtColor(PICAM.read(), cv2.COLOR_BGR2BGRA), MAPLX, MAPLY, cv2.INTER_AREA, borderMode=cv2.BORDER_TRANSPARENT))
