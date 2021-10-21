import time
from imutils.video import VideoStream
import imagezmq
import cv2
import numpy as np
from threading import *
import socket
import pyzmq


PC_IPs = {'whatever': 'tcp://169.254.165.116:5555'}
RB_MAIN_IP = "tcp://mainraspberry:5555"
PC_IP = PC_IPs['whatever']

#
# VOERT EEN KEER UIT
#

'''
Check if leaving videostream on affects performance
'''

# stuurt rechterfoto
picam = VideoStream(usePiCamera=True).start()
imageright = picam.read()
sender = imagezmq.ImageSender(connect_to=RB_MAIN_IP) 
sender.send_image(RB_IP_MAIN, imageright)

# ontvangt matrix
image_hub = imagezmq.ImageHub()
M = image_hub.recv_image()[1]
image_hub.send_reply(b'OK')
print(M)
print(type(M))

#
# HERHAALT
#

# maakt linkerfoto
imageleft = picam.read()

# transformeert foto

def warpImages(img1, H):
    rows1, cols1 = img1.shape[:2]
    rows2, cols2 = img2.shape[:2]

    list_of_points_1 = np.float32([[0, 0], [0, rows1], [cols1, rows1], [cols1, 0]]).reshape(-1, 1, 2)
    temp_points = np.float32([[0, 0], [0, rows2], [cols2, rows2], [cols2, 0]]).reshape(-1, 1, 2)

    # When we have established a homography we need to warp perspective
    # Change field of view
    list_of_points_2 = cv2.perspectiveTransform(temp_points, H)

    list_of_points = np.concatenate((list_of_points_1, list_of_points_2), axis=0)

    [x_min, y_min] = np.int32(list_of_points.min(axis=0).ravel() - 0.5)
    [x_max, y_max] = np.int32(list_of_points.max(axis=0).ravel() + 0.5)

    translation_dist = [-x_min, -y_min]

    H_translation = np.array([[1, 0, translation_dist[0]], [0, 1, translation_dist[1]], [0, 0, 1]])

    transformed_image = cv2.warpPerspective(imageleft, H_translation.dot(H), (x_max - x_min, y_max - y_min))
    return transformed_image

# stuurt foto naar andere pi
sender = imagezmq.ImageSender(connect_to='tcp://Laptop-Wout:5555')  # Input pc-ip (possibly webserver to sent to)
rpi_name = RB_IP_MAIN # send RPi hostname with each image
image = warpImages(imageleft, M)
sender.send_image(rpi_name, image)