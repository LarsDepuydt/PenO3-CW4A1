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
# USE_KEYPOINT_TRANSLATE = bool(argv[1])
RESOLUTION = WIDTH, HEIGHT = [int(x) for x in argv[2].split(",")]
# BLEND_FRAC = float(argv[3])
# X_t = int(argv[4])
# PC_IP = argv[5]

# ==============================
# CONSTANTS
# ==============================

CAMERAMODE = 1 # 1 = imutils.VideoStream, 2 = cv2.VideoCapture

FOCAL_LEN = 315 # focal length = 3.15mm volgens waveshare.com/imx219-d160.htm
s = 0 # skew parameter
KL = np.array([[FOCAL_LEN, s, WIDTH/2], [0, FOCAL_LEN, HEIGHT/2], [0, 0, 1]], dtype=np.uint16)  # mock intrinsics
KR = np.array([[FOCAL_LEN, 0, WIDTH/2], [0, FOCAL_LEN, HEIGHT/2], [0, 0, 1]], dtype=np.uint16)  # mock intrinsics
# [fx s x0; 0 fy y0; 0 0 1]

if CAMERAMODE == 1:
    PICAM = VideoStream(usePiCamera=True, resolution=RESOLUTION).start()
elif CAMERAMODE ==2:
    PICAM = cv2.VideoCapture(0)
    PICAM.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    PICAM.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
IMAGE_HUB = imagezmq.ImageHub()

RB_IP_MAIN, ready = IMAGE_HUB.recv_image()
if ready[0] == "ready":
    print("Received ready message")

sleep(1)  # allow camera sensor to warm up and wait to make sure helper is running
SENDER = imagezmq.ImageSender(connect_to=RB_IP_MAIN)

# ==============================
# INITIALISATION
# ==============================

IMAGE_HUB.send_reply(b'OK') # main continues after this and also takes picture
imgL = PICAM.read()
SENDER.send_image("", imgL)
print("Left calibration image was received by main")

MAPL1, MAPL2 = IMAGE_HUB.recv_image()[1]
IMAGE_HUB.send_reply(b'OK')
print("Received MAPL1 and MAPL2")

# ==============================
# LOOP
# ==============================

while True:
    SENDER.send_image("", cv2.remap(cv2.cvtColor(PICAM.read(), cv2.COLOR_BGR2BGRA), MAPL1, MAPL2, cv2.INTER_AREA, borderMode=cv2.BORDER_TRANSPARENT))
