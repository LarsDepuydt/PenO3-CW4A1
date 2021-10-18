import cv2
import numpy as np
import time
print(time.process_time())


t_start = time.perf_counter()
# variables
PATH1 = "../../images/testing_images_pi/lokaal/image_for_testing_1.jpg"
PATH2 = "../../images/testing_images_pi/lokaal/image_for_testing_2.jpg"
PATH_RESULT = "../../images/stitched_images/stitchted.jpg"
MATRIX_DATA = "matrix_data.txt"
smoothing_window_size = 800
height_panorama = 2464
width_panorama = 5000
width_img1 = 3280

# Load images
img1 = cv2.imread("../../images/testing_images_pi/lokaal/image_for_testing_2.jpg")
img2 = cv2.imread("../../images/testing_images_pi/lokaal/image_for_testing_1.jpg")


def warpImages(img1, img2, H):
    panorama1 = np.zeros((height_panorama, width_panorama, 3))
    mask1 = create_mask(img1, img2, height_panorama, width_panorama, version='left_image')
    panorama1[0:height_panorama, 0:width_img1, :] = img1
    panorama1 *= mask1
    mask2 = create_mask(img1, img2, height_panorama, width_panorama, version='right_image')
    smt = cv2.warpPerspective(img2, H, (width_panorama, height_panorama))
    panorama2 = smt * mask2
    output_img = panorama1 + panorama2
    print(time.perf_counter() - t_start)

    "output_img = result[0:2464, 0:5175, :]"
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

# Establish a homography
H = np.loadtxt("../MAIN_code/matrix_data.txt")
final_result = warpImages(img2, img1, H)
cv2.imwrite('Stitch_Blurr.jpg', final_result)
print(time.process_time())