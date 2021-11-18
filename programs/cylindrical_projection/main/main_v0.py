from imutils.video import VideoStream
import imagezmq
import numpy as np
import cv2
from time import sleep
import os

# =============================
# CONSTANTS
# =============================

CAMERAMODE = 1 # 1: imutilsVideostream, 2: cv2.VideoCapture
CALIBRATION_RESOLUTION = (480, 368)
STREAM_RESOLUTION =      (480, 360)
RB_IP_MAIN =    'tcp://169.254.222.67:5555'
RB_IP_HELPER =  'tcp://169.254.165.116:5555'
#PC_IP =         'tcp://192.168.137.1:5555'
#PC_IP = 'tcp://169.254.62.171:5555'
PC_IP = 'tcp://169.254.236.78:5555'

INIT_HELPER_CMD = "sh ssh_conn_and_execute_cmd.sh 'cd Desktop/PenO3-CW4A1/programs/MAIN_code/non_multi_threaded;python3 ./helper_v3.py'"

KEYPOINTS_COUNT = 2000  # set number of keypoints
MIN_MATCH_COUNT = 10  # Set minimum match condition
MATRIX_DATA = "matrix_data.txt"

CAMERA_MATRIX = [
    [320.68838395,   0, 315.79552501],
    [0, 314.07165737, 251.72067641],
    [ 0, 0, 1]]

total_image = None
imagelist = [None, None, None]

# =============================
# INITIALIZATION
# =============================

#os.system(INIT_HELPER_CMD)       # init helper pi
if CAMERAMODE == 1:
    PICAM = VideoStream(usePiCamera=True, resolution=CALIBRATION_RESOLUTION).start()
elif CAMERAMODE ==2:
    PICAM = cv2.VideoCapture(0)
    PICAM.set(cv2.CAP_PROP_FRAME_WIDTH, CALIBRATION_RESOLUTION[0])
    PICAM.set(cv2.CAP_PROP_FRAME_HEIGHT, CALIBRATION_RESOLUTION[1])
IMAGE_HUB = imagezmq.ImageHub()
sleep(3.0)  # allow camera sensor to warm up and wait to make sure helper is running
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

def cyl_project():
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



#M = trans_matrix_gen(image_left, image_right, KEYPOINTS_COUNT, MIN_MATCH_COUNT, MATRIX_DATA)
import TransformationMatricesForTesting as TMfT
M = TMfT.giveMildM()

SENDER.send_image(RB_IP_MAIN, M)
print("Transformation matrix sent & received")

# =============================
# STREAM
# =============================
#PICAM.close()
#PICAM = VideoStream(usePiCamera=True, resolution=STREAM_RESOLUTION).start()
SENDER = imagezmq.ImageSender(connect_to=PC_IP)

cols_r, rows_r = CALIBRATION_RESOLUTION
image_src_points = np.float32([[0, 0], [0, rows_r], [cols_r, rows_r], [cols_r, 0]]).reshape(-1, 1, 2)

image_dst_points = cv2.perspectiveTransform(image_src_points, M)
list_of_points = np.concatenate((image_src_points, image_dst_points), axis=0)
[x_min, y_min] = np.int32(list_of_points.min(axis=0).ravel() - 0.5)
# [x_max, y_max] = np.int32(list_of_points.max(axis=0).ravel() + 0.5)
translation_dist = [-x_min, -y_min]


while False:
    
    imagelist[0] = PICAM.read()
    imagelist[1] = IMAGE_HUB.recv_image()[1]
    imagelist[1][
            translation_dist[1] : rows_r+translation_dist[1],
            translation_dist[0] : cols_r+translation_dist[0]
            ] = imagelist[0]
    SENDER.send_image(RB_IP_MAIN, imagelist[1])
    IMAGE_HUB.send_reply(b'OK')


print("main_v2.py ENDED")







