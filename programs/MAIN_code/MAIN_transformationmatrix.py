import cv2
import numpy as np
import time
t_start = time.perf_counter()

# VARIABLES

PATH1 = "../../images/testing_images_pi/lokaal/image_for_testing_2.jpg"
PATH2 = "../../images/testing_images_pi/lokaal/image_for_testing_1.jpg"

AANTAL_KEYPOINTS = 2000 # set number of keypoints
MIN_MATCH_COUNT = 10    # Set minimum match condition
MATRIX_DATA = "matrix_data.txt"


# Load images
img1 = cv2.imread(PATH1)
img2 = cv2.imread(PATH2)

# Create our ORB detector and detect keypoints and descriptors
orb = cv2.ORB_create(nfeatures=AANTAL_KEYPOINTS)

# Find the key points and descriptors with ORB
keypoints1, descriptors1 = orb.detectAndCompute(img1, None)
keypoints2, descriptors2 = orb.detectAndCompute(img2, None)

# Create a BFMatcher object.
# It will find all of the matching keypoints on two images
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

print("CPU tijd: ", time.perf_counter() - t_start)
print("totale tijd: ", time.process_time())
