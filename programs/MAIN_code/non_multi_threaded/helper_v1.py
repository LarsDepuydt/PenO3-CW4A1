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

# WAIT FOR 
imageleft = picam.read()
sender = imagezmq.ImageSender(connect_to=RB_IP_MAIN)


sender.send_image(RB_IP_HELPER, imageleft)
print("Left calibration image sent.")


print('links')
sender = imagezmq.ImageSender(connect_to=RB_IP_MAIN)  # Input pc-ip (possibly webserver to sent to)
sender.send_image(RB_IP_HELPER, imageleft)
print('verzonden')
=======
sender = imagezmq.ImageSender(connect_to=RB_IP_MAIN)  # Input pc-ip (possibly webserver to sent to)
sender.send_image(RB_IP_MAIN, imageleft)
>>>>>>> d1ab157354edf460cd7ac2d685773fead657535a
>>>>>>> f99877c8343c4cabd9454e579e6548357d93fb2b

# Receives matrix
print("Waiting for tranformation matrix ...")
M = image_hub.recv_image()[1]
print("Received transformation matrix.")
image_hub.send_reply(b'OK')
print("Transformation matrix: \n", M)


left_image, output_image = None, None
image_list = [left_image, output_image]
i = 0

while True:
    print("In loop. Iteration ", i)
    i += 1
    # take image
    print('in while')
    image_list[0] = picam.read()

    #transform image
    print("erin transform")
    rows1, cols1 = image_list[0].shape[:2]
    print("1")
    list_of_points_1 = np.float32([[0, 0], [0, rows1], [cols1, rows1], [cols1, 0]]).reshape(-1, 1, 2)
    print("2")
    temp_points = np.float32([[0, 0], [0, rows1], [cols1, rows1], [cols1, 0]]).reshape(-1, 1, 2)
    print("3")

    # When we have established a homography we need to warp perspective
    # Change field of view
    print(M)
    print(temp_points)
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