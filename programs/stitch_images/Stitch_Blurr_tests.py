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
EXTRA_WIDTH = 1720
OFFSET = 400
BARRIER = WIDTH_IMG1 - OFFSET


t_start = time.perf_counter()

def main():
    # create masks
    left_mask = create_mask(BARRIER, version='left_image')
    right_mask = create_mask(BARRIER, version='right_image')

    # Loop to process all files
    # print(time.process_time())
    img1 = cv2.imread(PATH1)
    img2 = cv2.imread(PATH2)
    # img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    # img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    # Establish a homography
    H = np.loadtxt(MATRIX_DATA)
    final_result = warpImages(img2, img1, H, left_mask, right_mask)
    #print(time.process_time())
    cv2.imwrite('Stitch_Blurr.jpg', final_result)

    # print("CPU tijd: ", time.perf_counter() - t_start)
    # print("totale tijd: ", time.process_time())


def warpImages(img2, img1, H, mask1, mask2):
    panorama1 = np.zeros((HEIGHT_PANORAMA, WIDTH_PANORAMA, 3))
    panorama1[0:HEIGHT_PANORAMA, 0:WIDTH_IMG1, :] = img1
    # panorama1 = np.append(img1, np.zeros((HEIGHT_PANORAMA, EXTRA_WIDTH, 3)), axis=1)
    panorama1 *= mask1
    smt = cv2.warpPerspective(img2, H, (WIDTH_PANORAMA, HEIGHT_PANORAMA))
    panorama2 = smt * mask2
    output_img = panorama1 + panorama2

    return panorama1


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
    total1 = 0
    n = 100
    i = 0
    while i != n:
        t_start = time.process_time()
        main()
        print(time.process_time() - t_start, i)
        total1 += time.process_time() - t_start
        i += 1

    print("average is", total1/n)



"""
Reference time: 1.9651666 CPU and 2.0965 total
Time with grayscale: 1.11 CPU and 1.4004 total
Time with append (without canvas): 1.8 CPU and 2.3017 total
Time with both: 1.2 CPU and 1.516 total
"""