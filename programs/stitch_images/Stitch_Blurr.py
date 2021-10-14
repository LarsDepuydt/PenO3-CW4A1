import sys
import cv2
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image
import time

t_start = time.perf_counter()
smoothing_window_size = 800

# Load images
img1 = cv2.imread(r"C:\Users\jonas\PycharmProjects\PenO3-CW4A1\images\testing_images_pi\lokaal\image_for_testing_2.jpg")
img2 = cv2.imread(r"C:\Users\jonas\PycharmProjects\PenO3-CW4A1\images\testing_images_pi\lokaal\image_for_testing_1.jpg")

# Create our ORB detector and detect keypoints and descriptors
orb = cv2.ORB_create(nfeatures=2000)

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


def warpImages(img1, img2, H):
    print(time.perf_counter() - t_start)
    height_img1 = img1.shape[0]
    width_img1 = img1.shape[1]
    width_img2 = img2.shape[1]
    height_panorama = height_img1
    width_panorama = width_img1 + width_img2

    panorama1 = np.zeros((height_panorama, width_panorama, 3))
    mask1 = create_mask(img1, img2, version='left_image')
    panorama1[0:img1.shape[0], 0:img1.shape[1], :] = img1
    panorama1 *= mask1
    mask2 = create_mask(img1, img2, version='right_image')
    smt = cv2.warpPerspective(img2, H, (width_panorama, height_panorama))
    panorama2 = smt * mask2
    output_img = panorama1 + panorama2


    '''rows, cols = np.where(result[:, :, 0] != 0)
    min_row, max_row = min(rows), max(rows) + 1
    min_col, max_col = min(cols), max(cols) + 1
    output_img = result[min_row:max_row, min_col:max_col, :]'''
    return output_img


# Set minimum match condition
MIN_MATCH_COUNT = 10


def create_mask(img1, img2, version):

    height_img1 = img1.shape[0]
    width_img1 = img1.shape[1]
    width_img2 = img2.shape[1]
    height_panorama = height_img1
    width_panorama = width_img1 + width_img2
    offset = int(smoothing_window_size / 2)
    barrier = img1.shape[1] - int(smoothing_window_size / 2)
    mask = np.zeros((height_panorama, width_panorama))
    if version == 'left_image':
        mask[:, barrier - offset:barrier + offset] = np.tile(np.linspace(1, 0, 2 * offset).T, (height_panorama, 1))
        mask[:, :barrier - offset] = 1
    else:
        mask[:, barrier - offset:barrier + offset] = np.tile(np.linspace(0, 1, 2 * offset).T, (height_panorama, 1))
        mask[:, barrier + offset:] = 1
    return cv2.merge([mask, mask, mask])


if len(good) > MIN_MATCH_COUNT:
    # Convert keypoints to an argument for findHomography
    src_pts = np.float32([keypoints1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([keypoints2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    # Establish a homography
    H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    final_result = warpImages(img2, img1, H)
    cv2.imwrite('Stitch_Blurr.jpg', final_result)

else:
    print("Overlap was not good enough")

print(time.perf_counter() - t_start)