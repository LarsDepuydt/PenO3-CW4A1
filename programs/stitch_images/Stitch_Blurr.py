import sys
import cv2
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image
import time


t_start = time.perf_counter()
# variables
PATH1 = "../../images/testing_images_pi/lokaal/image_for_testing_1.jpg"
PATH2 = "../../images/testing_images_pi/lokaal/image_for_testing_2.jpg"
PATH_RESULT = "../../images/stitched_images/stitchted.jpg"
MATRIX_DATA = "matrix_data.txt"
smoothing_window_size = 200


def warpImages(img2, img1, H):
    height_panorama, width_img1 = img1.shape[:2]
    width_img2 = img2.shape[1]
    width_panorama = width_img1 + width_img2

    panorama1 = np.zeros((height_panorama, width_panorama, 3))
    mask1 = create_mask(img1, img2, height_panorama, width_panorama, version='left_image')
    panorama1[0:height_panorama, 0:width_img1, :] = img1
    panorama1 *= mask1
    cv2.imwrite("panorama1.jpg", panorama1)
    mask2 = create_mask(img1, img2, height_panorama, width_panorama, version='right_image')
    smt = cv2.warpPerspective(img2, H, (width_panorama, height_panorama))
    panorama2 = smt * mask2
    cv2.imwrite("panorama2.jpg", panorama2)
    output_img = panorama1 + panorama2
    print(time.perf_counter() - t_start)


    '''rows, cols = np.where(result[:, :, 0] != 0)
    min_row, max_row = min(rows), max(rows) + 1
    min_col, max_col = min(cols), max(cols) + 1
    output_img = result[min_row:max_row, min_col:max_col, :]'''
    return output_img

def create_mask(img1, img2, height_panorama, width_panorama, version):

    offset = int(smoothing_window_size / 2)
    barrier = img1.shape[1] - offset
    mask = np.zeros((height_panorama, width_panorama))
    if version == 'left_image':
        mask[:, barrier - offset:barrier + offset] = np.tile(np.linspace(1, 0, 2 * offset).T, (height_panorama, 1))
        mask[:, :barrier - offset] = 1
    else:
        mask[:, barrier - offset:barrier + offset] = np.tile(np.linspace(0, 1, 2 * offset).T, (height_panorama, 1))
        mask[:, barrier + offset:] = 1
    return cv2.merge([mask, mask, mask])

# Load images
img1 = cv2.imread(PATH2)
img2 = cv2.imread(PATH1)

# load tranformation matrix

M = np.loadtxt("../../programs/MAIN_code/matrix_data.txt")
print(M)
if len(M) > 0:
    result = warpImages(img1, img2, M)
    cv2.imwrite(PATH_RESULT, result)
else:
    print("No transformation matrix found")
print(time.perf_counter() - t_start)
