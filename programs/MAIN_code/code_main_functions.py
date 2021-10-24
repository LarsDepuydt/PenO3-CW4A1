import threading
from time import sleep
from imutils.video import VideoStream
import imagezmq
import cv2
import numpy as np

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

#
# MOET HERHALEN
#
right_image = None
left_image = None
total_image = None


def take_right_image:
    picam = VideoStream(usePiCamera=True).start()
    global right_image
    right_image = picam.read()


class receive_left_image(threading.Thread):
    def run(self):
        image_hub = imagezmq.ImageHub()
        rpi_name, imageleft = image_hub.recv_image()
        image_hub.send_reply(b'OK')
        global left_image
        left_image = imageleft


class merge_images(threading.Thread):
    def __init__(self, img_l, img_r, H):
        self.img_l = img_l
        self.img_r = img_r
        self.H = H

    def run(self):
        rows1, cols1 = self.img_r.shape[:2]
        rows2, cols2 = self.img_l.shape[:2]

        list_of_points_1 = np.float32([[0, 0], [0, rows1], [cols1, rows1], [cols1, 0]]).reshape(-1, 1, 2)
        temp_points = np.float32([[0, 0], [0, rows2], [cols2, rows2], [cols2, 0]]).reshape(-1, 1, 2)

        # When we have established a homography we need to warp perspective
        # Change field of view
        list_of_points_2 = cv2.perspectiveTransform(temp_points, self.H)
        list_of_points = np.concatenate((list_of_points_1, list_of_points_2), axis=0)

        [x_min, y_min] = np.int32(list_of_points.min(axis=0).ravel() - 0.5)
        # [x_max, y_max] = np.int32(list_of_points.max(axis=0).ravel() + 0.5)

        translation_dist = [-x_min, -y_min]

        output_img = self.img_l
        output_img[translation_dist[1]:rows1 + translation_dist[1],
        translation_dist[0]:cols1 + translation_dist[0]] = self.img_r

        global total_image
        total_image = output_img


class send_to_display(threading.Thread):
    def __init__(self, output_img):
        self.output_img = output_img
    def run(self):
        sender = imagezmq.ImageSender(
            connect_to='tcp://Laptop-Wout:5555')  # Input pc-ip (possibly webserver to sent to)
        sender.send_image(rpi_name, self.output_img)

step_1 = take_right_image()
step_2 = receive_left_image()
step_3 = merge_images(left_image, right_image, M)
step_4 = send_to_display(total_image)

while True:
    step_1.start()
    sleep(0.001)
    step_2.start()
    sleep(0.001)
    step_3.start()
    sleep(0.001)
    step_4.start()