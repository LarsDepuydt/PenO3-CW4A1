import threading
from time import sleep
from imutils.video import VideoStream
from picamera import PiCamera
import imagezmq
import cv2
import numpy as np

NETWORKS = {"jasper": "192.168.137",
           "robin": "...",
           "wout": "..."}

RB_MAIN_IP = "tcp://169.254.222.67:5555"
RB_HELPER_IP = "tcp://169.254.165.116:5555"


RESOLUTION = (720, 480)
FPS = 24


# INITIALIZE IMAGE HUB & CAMERA
image_hub = imagezmq.ImageHub()
picam = VideoStream(usePiCamera=True, resolution=RESOLUTION, framerate=FPS).start()
sleep(2.0) # allow camera sensor to warm up

# TAKE RIGHT PICTURE
imageright = picam.read()

# RECEIVE LEFT PICTURE
imageleft = image_hub.recv_image()[1]
image_hub.send_reply(b'OK')

cv2.imwrite("./image_left.jpg", imageleft)
cv2.imwrite("./image_right.jpg", imageright)


KEYPOINTS_COUNT = 2000  # set number of keypoints
MIN_MATCH_COUNT = 10  # Set minimum match condition
MATRIX_DATA = "matrix_data.txt"


right_image, left_image, total_image = None, None, None
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
    good_matches = []
    for m, n in matches:
        if m.distance < 0.6 * n.distance:
            good_matches.append(m)
    print("keypoints: ", keypoints, "| matches: ", len(matches), "| good matches:", len(good_matches))
    
    assert len(good_matches) >= min_mat

    # Convert keypoints to an argument for findHomography
    src_pts = np.float32([keypoints1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([keypoints2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    # Establish a homography
    M, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    print("Transformation Matrix : \n", M)
    np.savetxt(mat_data, M)
    return M


M = trans_matrix_gen(imageleft, imageright, KEYPOINTS_COUNT, MIN_MATCH_COUNT, MATRIX_DATA)
sender.send_image(RB_MAIN_IP, M)

i = 0
while True:
    print("In while, iteration: " i)
    i += 1
    
    #receive left image
    rpi_name, imageleft = image_hub.recv_image()
    image_hub.send_reply(b'OK')
    imagelist[1] = imageleft
    print("received left image")
    
    #take
    #picam = VideoStream(usePiCamera=True).start()
    imagelist[0] = picam.read()
    print("taken right image", i)

    #merge
    rows1, cols1 = imagelist[0].shape[:2]
    rows2, cols2 = imagelist[1].shape[:2]

    list_of_points_1 = np.float32([[0, 0], [0, rows1], [cols1, rows1], [cols1, 0]]).reshape(-1, 1, 2)
    temp_points = np.float32([[0, 0], [0, rows2], [cols2, rows2], [cols2, 0]]).reshape(-1, 1, 2)
    print("merge", i)

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