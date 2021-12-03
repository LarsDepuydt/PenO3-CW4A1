import numpy as np
import cv2
import imagezmq
from imutils.video import VideoStream
from time import sleep

# ==============================
# CONSTANTS
# ==============================

CAMERAMODE = 2 # 1 = imutils.VideoStream, 2 = cv2.VideoCapture
CALIBRATION_RESOLUTION = WIDTH, HEIGHT = (640, 480)
STREAM_RESOLUTION      = (640, 480)
RB_IP_MAIN =    'tcp://169.254.222.67:5555'
RB_IP_HELPER =  'tcp://169.254.165.116:5555'
#PC_IP =         'tcp://192.168.137.1:5555'
#PC_IP = 'tcp://169.254.62.171:5555'
#PC_IP = 'tcp://169.254.236.78:5555'
PREVIOUS_CALIBRATION_DATA_PATH = "calibration_data.txt"

INIT_HELPER_CMD = "sh ssHEIGHTconn_and_execute_cmd.sh 'cd Desktop/PenO3-CW4A1/programs/MAIN_code/non_multi_threaded;python3 ./helper_v3.py'"
#os.system(INIT_HELPER_CMD)       # init helper pi

KEYPOINT_COUNT = 2000  # set number of keypoints
MAX_MATCH_Y_DISP = 20 # maximum vertical displacement of valid match in pixels
MIN_MATCH_COUNT = 5  # set minimum number of better_matches
KEYPOINT_MASK_X_BOUND = 0.4 # only search for keypoints in this fraction of pixel towards the bound

# focal length = 3.15mm volgens waveshare.com/imx219-d160.htm
FOCAL_LEN_L_X = 315
FOCAL_LEN_L_Y = 315
FOCAL_LEN_R_X = 315
FOCAL_LEN_R_Y = 315
s = 0 # skew parameter

KL = np.array([[FOCAL_LEN_L_X, s, WIDTH/2], [0, FOCAL_LEN_L_Y, HEIGHT/2], [0, 0, 1]], dtype=np.uint16)  # mock intrinsics
KR = np.array([[FOCAL_LEN_R_X, 0, WIDTH/2], [0, FOCAL_LEN_R_Y, HEIGHT/2], [0, 0, 1]], dtype=np.uint16)  # mock intrinsics
# [fx s x0; 0 fy y0; 0 0 1]

if CAMERAMODE == 1:
    PICAM = VideoStream(usePiCamera=True, resolution=CALIBRATION_RESOLUTION).start()
elif CAMERAMODE ==2:
    PICAM = cv2.VideoCapture(0)
    PICAM.set(cv2.CAP_PROP_FRAME_WIDTH, CALIBRATION_RESOLUTION[0])
    PICAM.set(cv2.CAP_PROP_FRAME_HEIGHT, CALIBRATION_RESOLUTION[1])
IMAGE_HUB = imagezmq.ImageHub()

sleep(2)  # allow camera sensor to warm up and wait to make sure helper is running
SENDER = imagezmq.ImageSender(connect_to=RB_IP_HELPER)

if IMAGE_HUB.recv_image[1] == np.array(['ready']):
    pass
imgL = PICAM.read()
SENDER.send_image(imgL)

# ==============================
# INITIALISATION
# ==============================

SENDER.send_image(RB_IP_MAIN, np.array(["ready"]))
print("Ready message was received by helper")

imgR = PICAM.read()
imgL = IMAGE_HUB.recv_image[1]
IMAGE_HUB.send_reply(b'OK')

MAPL1, MAPL2 = IMAGE_HUB.recv_image[1]
IMAGE_HUB.send_reply(b'OK')
print('Received MAPL1 and MAPL2')

while True:
    SENDER.sendimage(cv2.remap(PICAM.read(), MAPL1, MAPL2, cv2.INTER_AREA, borderMode=cv2.BORDER_TRANSPARENT))
