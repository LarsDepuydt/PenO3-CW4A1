import cv2
import numpy as np
import time
print(time.process_time())

# variables
PATH1 = "../../images/testing_images_pi/lokaal/image_for_testing_1.jpg"
PATH2 = "../../images/testing_images_pi/lokaal/image_for_testing_2.jpg"
PATH_RESULT = "../../images/stitchted.jpg"
MATRIX_DATA = "../MAIN_code/matrix_data.txt"
HEIGHT_PANORAMA = 2464
WIDTH_PANORAMA = 5000
WIDTH_IMG1 = 3280
OFFSET = 400
BARRIER = WIDTH_IMG1 - OFFSET


t_start = time.perf_counter()

def main():
    # create masks
    img1 = cv2.imread(PATH1)
    img2 = cv2.imread(PATH2)
    left_mask = create_mask(BARRIER, version='left_image')
    right_mask = create_mask(BARRIER, version='right_image')

    # Loop to process all files
    print(time.process_time())
    img1 = cv2.imread(PATH1)
    img2 = cv2.imread(PATH2)

    # Establish a homography
    H = np.loadtxt(MATRIX_DATA)
    final_result = warpImages(img2, img1, H, left_mask, right_mask)
    print(time.process_time())
    cv2.imwrite('Stitch_Blurr.jpg', final_result)

    print("CPU tijd: ", time.perf_counter() - t_start)
    print("totale tijd: ", time.process_time())


def warpImages(img2, img1, H, mask1, mask2):
    panorama1 = np.zeros((HEIGHT_PANORAMA, WIDTH_PANORAMA, 3))
    panorama1[0:HEIGHT_PANORAMA, 0:WIDTH_IMG1, :] = img1
    panorama1 *= mask1
    smt = cv2.warpPerspective(img2, H, (WIDTH_PANORAMA, HEIGHT_PANORAMA))
    panorama2 = smt * mask2
    output_img = panorama1 + panorama2

    return output_img


def create_mask(barrier, version):
    mask = np.zeros((HEIGHT_PANORAMA, WIDTH_PANORAMA))
    if version == 'left_image':
        mask[:, barrier - OFFSET:barrier + OFFSET] = np.tile(np.linspace(1, 0, 2 * OFFSET).T, (HEIGHT_PANORAMA, 1))
        mask[:, :barrier - OFFSET] = 1
    else:
        mask[:, barrier - OFFSET:barrier + OFFSET] = np.tile(np.linspace(0, 1, 2 * OFFSET).T, (HEIGHT_PANORAMA, 1))
        mask[:, barrier + OFFSET:] = 1
    return cv2.merge([mask, mask, mask])

if __name__ == '__main__':
    main()