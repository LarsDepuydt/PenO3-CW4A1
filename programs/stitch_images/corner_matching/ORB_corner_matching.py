import cv2
from matplotlib import pyplot as plt

img1 = cv2.imread('../../../images/testing_images_pi/lokaal/image_for_testing_2.jpg', cv2.COLOR_BGR2GRAY) # queryImage
img2 = cv2.imread('../../../images/testing_images_pi/lokaal/image_for_testing_3.jpg', cv2.COLOR_BGR2GRAY) # trainImage
# Initiate SIFT detector
orb = cv2.ORB_create()

# find the keypoints and descriptors with SIFT
kp1, des1 = orb.detectAndCompute(img1,None)
kp2, des2 = orb.detectAndCompute(img2,None)
# create BFMatcher object
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
# Match descriptors.
matches = bf.match(des1,des2)

# Sort them in the order of their distance.
matches = sorted(matches, key = lambda x:x.distance)
# Draw first 10 matches.
img3 = cv2.drawMatches(img1,kp1,img2,kp2,matches[:10],None, flags=2)

plt.imshow(img3),plt.show()