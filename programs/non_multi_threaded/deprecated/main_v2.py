from imutils.video import VideoStream
import imagezmq
import numpy as np
import cv2
from time import sleep
import os

# =============================
# CONSTANTS
# =============================
sleep(5)
CALIBRATION_RESOLUTION = (480, 360)
STREAM_RESOLUTION =      (480, 360)
RB_IP_MAIN =    'tcp://169.254.222.67:5555'
RB_IP_HELPER =  'tcp://169.254.165.116:5555'
#PC_IP =         'tcp://192.168.137.1:5555'
PC_IP = 'tcp://169.254.62.171:5555'
INIT_HELPER_CMD = "sh ssh_conn_and_execute_cmd.sh 'cd Desktop/PenO3-CW4A1/programs/MAIN_code/non_multi_threaded;python3 ./helper_v2.py'"

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
print("Transformation matrix sent & received")

# =============================
# STREAM
# =============================
#PICAM.close()
#PICAM = VideoStream(usePiCamera=True, resolution=STREAM_RESOLUTION).start()
SENDER = imagezmq.ImageSender(connect_to=PC_IP)

i = 0
while i < 1:
    print("In while, iteration: ", i)
    i += 1
    
    #receive left image
    image_left = IMAGE_HUB.recv_image()[1]
    IMAGE_HUB.send_reply(b'OK')
    imagelist[1] = image_left
    print("Received left image")
    
    #take right image
    imagelist[0] = PICAM.read()
    print("Took right image")

    #merge
    rows_r, cols_r = imagelist[0].shape[:2]
    rows_l, cols_l = imagelist[1].shape[:2]

    image_src_points = np.float32([[0, 0], [0, rows_r], [cols_r, rows_r], [cols_r, 0]]).reshape(-1, 1, 2)
    print("merge")

    # 
    image_dst_points = cv2.perspectiveTransform(image_src_points, M)
    list_of_points = np.concatenate((image_src_points, image_dst_points), axis=0)

    [x_min, y_min] = np.int32(list_of_points.min(axis=0).ravel() - 0.5)
    # [x_max, y_max] = np.int32(list_of_points.max(axis=0).ravel() + 0.5)

    translation_dist = [-x_min, -y_min]

    output_img = imagelist[1]
    print(cols_r)
    print(rows_r)
    print(translation_dist[1])
    print(translation_dist[0])
    
    print(imagelist[0].shape)
    print(imagelist[1].shape)
    output_img[
            translation_dist[1] : rows_r+translation_dist[1],
            translation_dist[0] : cols_r+translation_dist[0]
            ] = imagelist[0]
    imagelist[2] = output_img
    cv2.imwrite("./left_image.jpg", imagelist[1])
    cv2.imwrite("./output_image.jpg", imagelist[2])
    print("Sending output_image to PC ...")
    SENDER.send_image(RB_IP_MAIN, imagelist[2])
    print("Output image sent")
    


print("main_v2.py ENDED")







