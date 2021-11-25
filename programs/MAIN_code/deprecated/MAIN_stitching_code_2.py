import cv2
import numpy as np
import time

t_start = time.perf_counter()
print(time.process_time())

# variables
PATH1 = "/home/pi/Desktop/PenO3-CW4A1/programs/cylindrical_projection/cylindrical_projection_images/left0_cyl.png"
PATH2 = "/home/pi/Desktop/PenO3-CW4A1/programs/cylindrical_projection/cylindrical_projection_images/right0_cyl.png"
PATH_RESULT = "stitchted_cyl.jpg"
MATRIX_DATA = "matrix_data.txt"

def warpImages(img1, img2, H):
    print("warp")
    print(time.process_time())
    rows1, cols1 = img1.shape[:2]

    list_of_points_1 = np.float32([[0, 0], [0, rows1], [cols1, rows1], [cols1, 0]]).reshape(-1, 1, 2)


    list_of_points_2 = cv2.perspectiveTransform(list_of_points_1, H)

    list_of_points = np.concatenate((list_of_points_1, list_of_points_2), axis=0)

    [x_min, y_min] = np.int32(list_of_points.min(axis=0).ravel() - 0.5)
    [x_max, y_max] = np.int32(list_of_points.max(axis=0).ravel() + 0.5)

    translation_dist = [-x_min, -y_min]

    H_translation = np.array([[1, 0, translation_dist[0]], [0, 1, 0], [0, 0, 1]])
    #output_img = cv2.warpPerspective(img2, H_translation.dot(I), (x_max - x_min, y_max - y_min))
    xplus = np.array([np.array([np.array([0, 0, 0]) for x in range(1, 700)]) for y in range(1, rows1+1)])
    print(type(xplus) ,type(xplus[0]))
    print(type(img1[0][0][0]), type(img2[0][0][0]))
    output_img = np.concatenate((img2, xplus), axis=1)
    output_img[translation_dist[1]:rows1 + translation_dist[1], translation_dist[0]:cols1 + translation_dist[0]] = img1
    print(time.process_time())
    cv2.imwrite('bla.png', output_img)
    cv2.imshow('h', output_img)
    cv2.waitKey(0)
    return output_img



# Load images
img1 = cv2.imread(PATH1)
img2 = cv2.imread(PATH2)
# load tranformation matrix

M = np.loadtxt(MATRIX_DATA)

if len(M) > 0:
    result = warpImages(img2, img1, M)
    cv2.imwrite(PATH_RESULT, result)
else:
    print("No transformation matrix found")
print(time.perf_counter() - t_start)

print("CPU tijd: ", time.perf_counter() - t_start)
print("totale tijd: ", time.process_time())
