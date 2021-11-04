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


CALIBRATION_RESOLUTION = (480, 368)
STREAM_RESOLUTION = (480, 360)
RB_IP_MAIN = 'tcp://169.254.222.67:5555'
RB_IP_HELPER = 'tcp://169.254.165.116:5555'



# =============================
# INITIALIZATION
# =============================

IMAGE_HUB = imagezmq.ImageHub()
PICAM = VideoStream(usePiCamera=True, resolution=CALIBRATION_RESOLUTION).start()
sleep(2.0)  # allow camera sensor to warm up
SENDER = imagezmq.ImageSender(connect_to=RB_IP_MAIN)

# WAIT FOR READY MESSAGE
ready_message = IMAGE_HUB.recv_image()[1]
assert ready_message == np.array(["ready"])
print("Received ready message")
IMAGE_HUB.send_reply(b'OK')

# CALIBRATION ---------------------

# Take and send left calibration image
SENDER.send_image(RB_IP_HELPER, PICAM.read())
print("Sent left calibration image")

M = IMAGE_HUB.recv_image()[1]
IMAGE_HUB.send_reply(b'OK')
print("Received transformation matrix")
print("M = ", M)

# =============================
# STREAM
# =============================
#PICAM.stop()
#PICAM = VideoStream(usePiCamera=True, resolution=STREAM_RESOLUTION).start()
i = 0
output_image = None
image_list = [None, None]

cols1 = CALIBRATION_RESOLUTION[1]
rows1 = CALIBRATION_RESOLUTION[0]
# transform image corner point an dput i n nested matrix
image_src_points = np.array([[0, 0], [0, rows1], [cols1, rows1], [cols1, 0]], dtype=np.float32).reshape(-1, 1, 2)
#nested coordinates necessary: seperate channels see opencv documentation
M = np.float32(M)   # MAKE SURE BOTH IMAGE_SRC_POINTS AND M ARE HAVE np.float32 ENTRIES!
image_dst_points = cv2.perspectiveTransform(image_src_points, M)
list_of_points = np.concatenate((image_src_points, image_dst_points), axis=0)
print(list_of_points)
print(list_of_points.min(axis=0))
print(list_of_points.min(axis=0).ravel())
print(np.int32(list_of_points.min(axis=0).ravel() - 0.5))
[x_min, y_min] = np.int32(list_of_points.min(axis=0).ravel() - 0.5)
[x_max, y_max] = np.int32(list_of_points.max(axis=0).ravel() + 0.5)
translation_dist = [-x_min, -y_min]
H_translation = np.array([[1, 0, translation_dist[0]], [0, 1, translation_dist[1]], [0, 0, 1]])

while i < 1:
    print("In loop. Iteration ", i)
    i += 1
    # take image
    image_list[0] = PICAM.read()
    #print(image_list)
    
    image_list[1] = cv2.warpPerspective(image_list[0], H_translation.dot(M), (x_max - x_min, y_max - y_min))

    #print('Sending warped image')
    SENDER.send_image(RB_IP_HELPER, image_list[1])
    #print('Sent warped image')
    
print("helper_v2.py ENDED")



