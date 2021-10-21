import time
from imutils.video import VideoStream
import pyzmq
import imagezmq
import cv2
import numpy as np
from threading import *
import socket


PC_IPs = {'whatever': 'tcp://169.254.165.116:5555'}
RB_HELPER_IP = "tcp://helperraspberry:5555"
PC_IP = PC_IPs]['whatever']


#
# MOET EERST RUNNEN, MAIN STAAT RECHTS
#

# ontvangt linkerfoto
image_hub = imagezmq.ImageHub()
rpi_name, imageleft = image_hub.recv_image()
image_hub.send_reply(b'OK')

# maakt rechterfoto
picam = VideoStream(usePiCamera=True).start()
imageright = picam.read()


# maakt transformatiematrix
AANTAL_KEYPOINTS = 2000 # set number of keypoints
MIN_MATCH_COUNT = 10    # Set minimum match condition
MATRIX_DATA = "matrix_data.txt"

img1 = imageleft
img2 = imageright

# Create our ORB detector and detect keypoints and descriptors
orb = cv2.ORB_create(nfeatures=AANTAL_KEYPOINTS)

# Find the key points and descriptors with ORB
keypoints1, descriptors1 = orb.detectAndCompute(img1, None)
keypoints2, descriptors2 = orb.detectAndCompute(img2, None)

# Create a BFMatcher object.
# It will find all of the matching key points on two images
bf = cv2.BFMatcher_create(cv2.NORM_HAMMING)

# Find matching points
matches = bf.knnMatch(descriptors1, descriptors2, k=2)

# Finding the best matches
good = []
for m, n in matches:
    if m.distance < 0.6 * n.distance:
        good.append(m)
print(len(matches), len(good))


if len(good) > MIN_MATCH_COUNT:
    # Convert keypoints to an argument for findHomography
    src_pts = np.float32([keypoints1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([keypoints2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    # Establish a homography
    M, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    print(M)
    np.savetxt(MATRIX_DATA, M)

else:
    print("Overlap was not good enough")

# STUUR MATRIX

sender = imagezmq.ImageSender(connect_to=RB_HELPER_IP)
sender.send_image(RB_MAIN_IP, M)


#
# MOET HERHALEN
#


def voeg_samen(img_l, img_r, H):
    rows1, cols1 = img_r.shape[:2]
    rows2, cols2 = img_l.shape[:2]

    list_of_points_1 = np.float32([[0, 0], [0, rows1], [cols1, rows1], [cols1, 0]]).reshape(-1, 1, 2)
    temp_points = np.float32([[0, 0], [0, rows2], [cols2, rows2], [cols2, 0]]).reshape(-1, 1, 2)

    # When we have established a homography we need to warp perspective
    # Change field of view
    list_of_points_2 = cv2.perspectiveTransform(temp_points, H)
    list_of_points = np.concatenate((list_of_points_1, list_of_points_2), axis=0)

    [x_min, y_min] = np.int32(list_of_points.min(axis=0).ravel() - 0.5)
    [x_max, y_max] = np.int32(list_of_points.max(axis=0).ravel() + 0.5)

    translation_dist = [-x_min, -y_min]

    output_img = img_l
    output_img[translation_dist[1]:rows1 + translation_dist[1], translation_dist[0]:cols1 + translation_dist[0]] = img_r

    return output_img

# maakt rechterfoto
picam = VideoStream(usePiCamera=True).start()
imageright = picam.read()

# ontvangt linkerfoto
image_hub = imagezmq.ImageHub()
rpi_name, imageleft = image_hub.recv_image()
image_hub.send_reply(b'OK')

# send to server/host pc
sender = imagezmq.ImageSender(connect_to=PC_IP)  # Input pc-ip (possibly webserver to sent to)
pc_name = PC_IP  # send RPi hostname with each image
image = voeg_samen(imageleft, imageright, M).read()
sender.send_image(rpi_name, image)
