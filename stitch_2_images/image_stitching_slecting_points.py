import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt

"""
def harris(img_dir):
    img = cv.imread(img_dir)
    gray = cv.cvtColor(img,cv.COLOR_BGR2GRAY)  # Turn image to gray

    harris = cv.cornerHarris(gray,2,3,0.04)  # Applies harris corner detector to gray image

    # Result is dilated for marking the corners, not important
    harris = cv.dilate(harris,None)

    # Threshold for an optimal value, it may vary depending on the image.
    img[harris>0.01*harris.max()]=[0,0,255]

    plt.figure("Harris detector")
    plt.imshow(cv.cvtColor(img, cv.COLOR_BGR2RGB)), plt.title("Harris")
    plt.xticks([]), plt.yticks([])
    plt.savefig('../mergeImages/Harris_detector', bbox_inches='tight')
    plt.show()

harris("../mergeImages/mergePart1.jpg")  # Change this path to one that will lead to your image
"""


# Code source: https://docs.opencv.org/master/da/df5/tutorial_py_sift_intro.html

# Read the image
img = cv.imread('../mergeImages/mergePart1.jpg')

# Convert to grayscale
gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

# Find the features (i.e. keypoints) and feature descriptors in the image
sift = cv.SIFT_create()
kp, des = sift.detectAndCompute(gray, None)

# Draw circles to indicate the location of features and the feature's orientation
img = cv.drawKeypoints(gray, kp, img, flags=cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

# Save the image
cv.imwrite('../mergeImages/sift_with_features.jpg', img)

