from imutils.video import VideoStream
import imagezmq
import numpy as np
import cv2
from time import sleep
import os

# =============================
# CONSTANTS
# =============================

CALIBRATION_RESOLUTION = (720, 480)
STREAM_RESOLUTION = (480, 360)
RB_IP_MAIN = 'tcp://169.254.222.67:5555'
RB_IP_HELPER = 'tcp://169.254.165.116:5555'
INIT_HELPER_CMD = "sh ssh_login_and_run_file.sh 'cd Desktop/PenO3-CW4A1/programs/MAIN_code/non_multi_threaded;python3 ./test_helper.py'"

KEYPOINTS_COUNT = 2000  # set number of keypoints
MIN_MATCH_COUNT = 10  # Set minimum match condition
MATRIX_DATA = "matrix_data.txt"

total_image = None
imagelist = [None, None, None]

# =============================
# INITIALIZATION
# =============================

os.system(INIT_HELPER_CMD)       # init helper pi
IMAGE_HUB = imagezmq.ImageHub()
PICAM = VideoStream(usePiCamera=True, resolution=CALIBRATION_RESOLUTION).start()
sleep(4.0)  # allow camera sensor to warm up and wait to make sure helper is running
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

M = trans_matrix_gen(image_left, image_right, KEYPOINTS_COUNT, MIN_MATCH_COUNT, MATRIX_DATA)
SENDER.send_image(RB_IP_MAIN, M)
print("Transformation matrix sent")

# =============================
# STREAM
# =============================




print("main_v2.py ENDED")







