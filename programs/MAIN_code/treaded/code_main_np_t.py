import threading
from time import sleep
from imutils.video import VideoStream
from picamera import PiCamera
import imagezmq
import cv2
import numpy as np

ETHERNET = "tcp://169.254.165.116:5555"
PC_IPs = {'whatever': 'tcp://169.254.165.116:5555', 'jasper': 'tcp://192.168.137.50'}
RB_HELPER_IP = ETHERNET
# RB_HELPER_IP = "tcp://helperraspberry:5555"
ETHERNET2 = "tcp://169.254.222.67:5555"
RB_MAIN_IP = ETHERNET2
# RB_MAIN_IP = "tcp://mainraspberry:5555"
PC_IP = PC_IPs['jasper']

# RECEIVE LEFT PICTURE
image_hub = imagezmq.ImageHub()
imageleft = image_hub.recv_image()[1]
image_hub.send_reply(b'OK')

# TAKE RIGHT PICTURE
picam = VideoStream(usePiCamera=True).start()
# picam.camera.resolution(640, 480)
# print(picam.__dict__)
sleep(2.0)
imageright = picam.read()

cv2.imwrite("./image_left.jpg", imageleft)
cv2.imwrite("./image_right.jpg", imageright)

KEYPOINTS_COUNT = 2000  # set number of keypoints
MIN_MATCH_COUNT = 10  # Set minimum match condition
MATRIX_DATA = "matrix_data.txt"

right_image = None
left_image = None
total_image = None
imagelist = [right_image, left_image, total_image]


def trans_matrix_gen(imgleft, imgright, keypoints, min_mat, mat_data):
    # Create our ORB detector and detect keypoints and descriptors
    orb = cv2.ORB_create(nfeatures=keypoints)

    # Find the key points and descriptors with ORB
    keypoints1, descriptors1 = orb.detectAndCompute(imgleft, None)
    keypoints2, descriptors2 = orb.detectAndCompute(imgright, None)

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
    print("matches: ", len(matches), "good matches:", len(good))

    assert len(good) >= min_mat

    # Convert keypoints to an argument for findHomography
    src_pts = np.float32([keypoints1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([keypoints2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    # Establish a homography
    M, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    print(M)
    np.savetxt(mat_data, M)
    return M


class TakeRightImage(threading.Thread):
    def __init__(self, lijst):
        super().__init__()
        self.lijst = lijst

    def run(self):
        while True:
            picam = VideoStream(usePiCamera=True).start()
            self.lijst[0] = picam.read()


class ReceiveLeftImage(threading.Thread):
    def __init__(self, lijst):
        super().__init__()
        self.lijst = lijst

    def run(self):
        while True:
            rpi_name, imageleft = image_hub.recv_image()
            image_hub.send_reply(b'OK')
            self.lijst[1] = imageleft


M = trans_matrix_gen(imageleft, imageright, KEYPOINTS_COUNT, MIN_MATCH_COUNT, MATRIX_DATA)

sender = imagezmq.ImageSender(connect_to=RB_HELPER_IP)
sender.send_image(RB_MAIN_IP, M)

step_1 = TakeRightImage(imagelist)
step_2 = ReceiveLeftImage(imagelist)


step_1.start()
sleep(0.001)
step_2.start()
sleep(0.001)


while True:
    if imagelist[0] != None and imagelist[1] != None:
        #merge
        rows1, cols1 = imagelist[0].shape[:2]
        rows2, cols2 = imagelist[1].shape[:2]

        list_of_points_1 = np.float32([[0, 0], [0, rows1], [cols1, rows1], [cols1, 0]]).reshape(-1, 1, 2)
        temp_points = np.float32([[0, 0], [0, rows2], [cols2, rows2], [cols2, 0]]).reshape(-1, 1, 2)

        # When we have established a homography we need to warp perspective
        # Change field of view
        list_of_points_2 = cv2.perspectiveTransform(temp_points, M)
        list_of_points = np.concatenate((list_of_points_1, list_of_points_2), axis=0)

        [x_min, y_min] = np.int32(list_of_points.min(axis=0).ravel() - 0.5)
        # [x_max, y_max] = np.int32(list_of_points.max(axis=0).ravel() + 0.5)

        translation_dist = [-x_min, -y_min]

        output_img = imagelist[1]
        output_img[translation_dist[1]:rows1 + translation_dist[1],
        translation_dist[0]:cols1 + translation_dist[0]] = imagelist[0]

        imagelist[2] = output_img

        #send
        sender = imagezmq.ImageSender(connect_to=PC_IP)  # Input pc-ip (possibly webserver to sent to)
        sender.send_image(RB_MAIN_IP, imagelist[2])
