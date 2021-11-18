from imutils.video import VideoStream
import imagezmq
import numpy as np
import cv2
from time import sleep
import os

# =============================
# CONSTANTS
# =============================

CAMERAMODE = 1  # 1: imutilsVideostream, 2: cv2.VideoCapture
CALIBRATION_RESOLUTION = (480, 368)
STREAM_RESOLUTION = (480, 360)
RB_IP_MAIN = 'tcp://169.254.222.67:5555'
RB_IP_HELPER = 'tcp://169.254.165.116:5555'
# PC_IP =         'tcp://192.168.137.1:5555'
# PC_IP = 'tcp://169.254.62.171:5555'
PC_IP = 'tcp://169.254.236.78:5555'

INIT_HELPER_CMD = "sh ssh_conn_and_execute_cmd.sh 'cd Desktop/PenO3-CW4A1/programs/MAIN_code/non_multi_threaded;python3 ./helper_v3.py'"

CILINDER_FACTOR = 0
TRANSLATIEAFSTAND = 0
ZWARTAFSTAND = 0
total_image = None
imagelist = [None, None, None]

# =============================
# INITIALIZATION
# =============================

# os.system(INIT_HELPER_CMD)       # init helper pi
if CAMERAMODE == 1:
    PICAM = VideoStream(usePiCamera=True, resolution=CALIBRATION_RESOLUTION).start()
elif CAMERAMODE == 2:
    PICAM = cv2.VideoCapture(0)
    PICAM.set(cv2.CAP_PROP_FRAME_WIDTH, CALIBRATION_RESOLUTION[0])
    PICAM.set(cv2.CAP_PROP_FRAME_HEIGHT, CALIBRATION_RESOLUTION[1])
IMAGE_HUB = imagezmq.ImageHub()
sleep(3.0)  # allow camera sensor to warm up and wait to make sure helper is running
SENDER = imagezmq.ImageSender(connect_to=RB_IP_HELPER)

# SEND READY MESSAGE
SENDER.send_image(RB_IP_MAIN, np.array(["ready"]))
print("Ready message was received by helper")

# CALIBRATION -------------
image_right = PICAM.read()
image_left = IMAGE_HUB.recv_image()[1]
IMAGE_HUB.send_reply(b'OK')
print("Received left calibration image")
cv2.imwrite("./calibration_image_left.jpg", image_left)
cv2.imwrite("./calibration_image_right.jpg", image_right)

h, w = image_right.shape[:2]
K = np.array([[CILINDER_FACTOR, 0, w / 2], [0, CILINDER_FACTOR, h / 2], [0, 0, 1]])


def cylindricalWarp(img, K):
    """This function returns the cylindrical warp for a given image and intrinsics matrix K"""
    h_, w_ = img.shape[:2]
    # pixel coordinates
    y_i, x_i = np.indices((h_, w_))
    X = np.stack([x_i, y_i, np.ones_like(x_i)], axis=-1).reshape(h_ * w_, 3)  # to homog
    Kinv = np.linalg.inv(K)
    X = Kinv.dot(X.T).T  # normalized coords
    # calculate cylindrical coords (sin\theta, h, cos\theta)
    A = np.stack([np.sin(X[:, 0]), X[:, 1], np.cos(X[:, 0])], axis=-1).reshape(w_ * h_, 3)
    #boven onder: A = np.stack([X[:, 0], np.sin(X[:, 1]), np.cos(X[:, 1])], axis=-1).reshape(w_ * h_, 3)
    B = K.dot(A.T).T  # project back to image-pixels plane
    # back from homog coords
    B = B[:, :-1] / B[:, [-1]]
    # make sure warp coords only within image bounds
    B[(B[:, 0] < 0) | (B[:, 0] >= w_) | (B[:, 1] < 0) | (B[:, 1] >= h_)] = -1
    B = B.reshape(h_, w_, -1)

    img_rgba = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)  # for transparent borders...
    # warp the image according to cylindrical coords
    return cv2.remap(img_rgba, B[:, :, 0].astype(np.float32), B[:, :, 1].astype(np.float32), cv2.INTER_AREA,
                     borderMode=cv2.BORDER_TRANSPARENT)



# =============================
# STREAM
# =============================
# PICAM.close()
# PICAM = VideoStream(usePiCamera=True, resolution=STREAM_RESOLUTION).start()

SENDER = imagezmq.ImageSender(connect_to=PC_IP)

while True:

    imagelist[0] = PICAM.read()
    imagelist[0] = cylindricalWarp(imagelist[0], K)

    imagelist[1] = IMAGE_HUB.recv_image()[1]

    imagelist[2] = np.concatenate((imagelist[:, 0:TRANSLATIEAFSTAND], img2[:, ZWARTAFSTAND:]), axis=1)

    SENDER.send_image(RB_IP_MAIN, imagelist[2])
    IMAGE_HUB.send_reply(b'OK')







