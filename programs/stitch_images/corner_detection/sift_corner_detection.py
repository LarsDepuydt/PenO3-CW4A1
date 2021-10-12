import cv2 as cv
import time
t_start = time.perf_counter()

# Code source: https://docs.opencv.org/master/da/df5/tutorial_py_sift_intro.html

# Read the image
img = cv.imread('../../../images/testing_images_pi/lokaal/image_for_testing_1.jpg')

# Convert to grayscale
gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

# Find the features (i.e. keypoints) and feature descriptors in the image
sift = cv.SIFT_create()
kp, des = sift.detectAndCompute(gray, None)

# Draw circles to indicate the location of features and the feature's orientation
img = cv.drawKeypoints(gray, kp, img, flags=cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

# Save the image
cv.imwrite('../../../images/testing_images_online/corners/sift_with_features.jpg', img)
print(time.perf_counter() - t_start)
print("done")
