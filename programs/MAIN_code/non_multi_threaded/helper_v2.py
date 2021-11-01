from imutils.video import VideoStream
import imagezmq
import numpy as np
import cv2
from time import sleep

# =============================
# CONSTANTS
# =============================

CALIBRATION_RESOLUTION = (720, 480)
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
print("Received transformation matrix")
print("M = ", M)

# =============================
# STREAM
# =============================
PICAM.stop()
PICAM = VideoStream(usePiCamera=True, resolution=STREAM_RESOLUTION).start()
i = 0

output_image = None
image_list = [None, None]

while True:
    print("In loop. Iteration ", i)
    i += 1
    # take image
    image_list[0] = PICAM.read()
    print(image_list)
    
    #transform image
    print("Into transorm")
    rows1, cols1 = image_list[0].shape[:2]
    print("1...")
    list_of_points_1 = np.float32([[0, 0], [0, rows1], [cols1, rows1], [cols1, 0]]).reshape(-1, 1, 2)
    print("2...")
    temp_points = np.float32([[0, 0], [0, rows1], [cols1, rows1], [cols1, 0]]).reshape(-1, 1, 2)
    print("Transform done")

    # When we have established a homography we need to warp perspective
    # Change field of view

    print("temp_points = ", temp_points)
    print("Into perspectiveTransform")
    list_of_points_2 = cv2.perspectiveTransform(temp_points, M)
    print("4")

    list_of_points = np.concatenate((list_of_points_1, list_of_points_2), axis=0)
    print("5")

    [x_min, y_min] = np.int32(list_of_points.min(axis=0).ravel() - 0.5)
    print("6")
    [x_max, y_max] = np.int32(list_of_points.max(axis=0).ravel() + 0.5)
    print("7")

    translation_dist = [-x_min, -y_min]
    print("8")

    H_translation = np.array([[1, 0, translation_dist[0]], [0, 1, translation_dist[1]], [0, 0, 1]])
    print("9")

    image_list[1] = cv2.warpPerspective(image_list[0], H_translation.dot(M), (x_max - x_min, y_max - y_min))
    print("10")

    # send output
    print('send output')
    sender.send_image(RB_IP_MAIN, image_list[1])
    print('na send output')

print("helper_v2.py ENDED")



