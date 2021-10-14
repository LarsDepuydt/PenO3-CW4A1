import cv2
import numpy as np
#import matplotlib.pyplot as plt

# VARIABLES

PATH1 = "../images/testing_images_pi/lokaal/image_for_testing_2.jpg"
PATH2 = "../images/testing_images_pi/lokaal/image_for_testing_3.jpg"
AANTAL_KEYPOINTS = 2000


# import images
img1_import = cv2.imread('../mergeImages/RightSide.jpg')
img2_import = cv2.imread('../mergeImages/LeftSide.jpg')

# color images to grey
img1 = cv2.cvtColor(img1_import, cv2.COLOR_BGR2GRAY)
img2 = cv2.cvtColor(img2_import, cv2.COLOR_BGR2GRAY)


# create ORB with number of keypoints
orb = cv2.ORB_create(nfeatures=AANTAL_KEYPOINTS)


# find the keypoints and descriptors with SIFT
kp1, des1 = orb.detectAndCompute(img1, None)
kp2, des2 = orb.detectAndCompute(img2, None)
# BFMatcher with default params
bf = cv2.BFMatcher()
matches = bf.knnMatch(des1, des2, k=2)

# print matches
# Apply ratio test
good = []
for m in matches:
    if m[0].distance < 0.5 * m[1].distance:
        good.append(m)
matches = np.asarray(good)

'''print matches[2,0].queryIdx
print matches[2,0].trainIdx
print matches[2,0].distance'''

if len(matches[:, 0]) >= 4:
    src = np.float32([kp1[m.queryIdx].pt for m in matches[:, 0]]).reshape(-1, 1, 2)
    dst = np.float32([kp2[m.trainIdx].pt for m in matches[:, 0]]).reshape(-1, 1, 2)

    H, masked = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
    print(H)
else:
    raise AssertionError("Can't find enough keypoints.")

dst = cv2.warpPerspective(img_, H, (img.shape[1] + img_.shape[1], img.shape[0]))
plt.subplot(122), plt.imshow(dst), plt.title('Warped Image')
plt.show()
plt.figure()
dst[0:img.shape[0], 0:img.shape[1]] = img
cv2.imwrite('resultant_stitched_panorama.jpg', dst)
plt.imshow(dst)
plt.show()
cv2.imwrite('resultant_stitched_panorama.jpg', dst)