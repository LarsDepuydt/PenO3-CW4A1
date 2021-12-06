from imutils.video import VideoStream
import imagezmq
import numpy as np
import cv2
from time import sleep
import sys
from copy import deepcopy

# =============================
# CONSTANTS
# =============================

CAMERAMODE = 1
CALIBRATION_RESOLUTION = (480, 368)
STREAM_RESOLUTION = (480, 360)
RB_IP_MAIN = 'tcp://169.254.222.67:5555'
RB_IP_HELPER = 'tcp://169.254.165.116:5555'
CILINDER_FACTOR = 0

# =============================
# INITIALIZATION
# =============================

IMAGE_HUB = imagezmq.ImageHub()
if CAMERAMODE == 1:
    PICAM = VideoStream(usePiCamera=True, resolution=CALIBRATION_RESOLUTION).start()
elif CAMERAMODE == 2:
    PICAM = cv2.VideoCapture(0)
    PICAM.set(cv2.CAP_PROP_FRAME_WIDTH, CALIBRATION_RESOLUTION[0])
    PICAM.set(cv2.CAP_PROP_FRAME_HEIGHT, CALIBRATION_RESOLUTION[1])
sleep(1.0)  # allow camera sensor to warm up
SENDER = imagezmq.ImageSender(connect_to=RB_IP_MAIN)

# WAIT FOR READY MESSAGE
print('waiting for ready...')
ready_message = IMAGE_HUB.recv_image()[1]
print("gottem")
assert ready_message == np.array(["ready"])
print("Received ready message")
IMAGE_HUB.send_reply(b'OK')

# CALIBRATION ---------------------

# Take and send left calibration image
img1 = PICAM.read()
SENDER.send_image(RB_IP_HELPER, img1)
print("Sent left calibration image")
h, w = img1.shape[:2]
K = np.array([[CILINDER_FACTOR, 0, w / 2], [0, CILINDER_FACTOR, h / 2], [0, 0, 1]])


# =============================
# STREAM
# =============================
# PICAM.stop()
# PICAM = VideoStream(usePiCamera=True, resolution=STREAM_RESOLUTION).start()

image_list = [None, None]


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



while True:
    SENDER.send_image(RB_IP_HELPER, cylindricalWarp(PICAM.read(), K))

    '''
    SENDER.send_image(RB_IP_HELPER, np.array([0]))
    image_list[0] = PICAM.read()
    image_list[1] = cv2.warpPerspective(image_list[0], R, S)
    SENDER.send_image(RB_IP_HELPER, image_list[1])
    '''

print("helper_v2.py ENDED")
