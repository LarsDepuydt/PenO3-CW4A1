import cv2
import numpy as np

# variables
PATH1 = "../images/testing_images_pi/lokaal/image_for_testing_1.jpg"
PATH2 = "../images/testing_images_pi/lokaal/image_for_testing_2.jpg"
PATH_RESULT = "../../images/stitched_images/stitchted.jpg"

def warpImages(img1, img2, H):
    rows1, cols1 = img1.shape[:2]
    rows2, cols2 = img2.shape[:2]

    list_of_points_1 = np.float32([[0, 0], [0, rows1], [cols1, rows1], [cols1, 0]]).reshape(-1, 1, 2)
    temp_points = np.float32([[0, 0], [0, rows2], [cols2, rows2], [cols2, 0]]).reshape(-1, 1, 2)

    # When we have established a homography we need to warp perspective
    # Change field of view
    list_of_points_2 = cv2.perspectiveTransform(temp_points, H)

    list_of_points = np.concatenate((list_of_points_1, list_of_points_2), axis=0)

    [x_min, y_min] = np.int32(list_of_points.min(axis=0).ravel() - 0.5)
    [x_max, y_max] = np.int32(list_of_points.max(axis=0).ravel() + 0.5)

    translation_dist = [-x_min, -y_min]

    H_translation = np.array([[1, 0, translation_dist[0]], [0, 1, translation_dist[1]], [0, 0, 1]])

    output_img = cv2.warpPerspective(img2, H_translation.dot(H), (x_max - x_min, y_max - y_min))
    output_img[translation_dist[1]:rows1 + translation_dist[1], translation_dist[0]:cols1 + translation_dist[0]] = img1

    return output_img



# Load images
img1 = cv2.imread(PATH1)
img2 = cv2.imread(PATH2)

# load tranformation matrix
M = np.loadtxt("MAIN_code/matrix_data.txt")


if len(M) > 0:
    result = warpImages(img2, img1, M)
    cv2.imwrite("stitchted.jpg", result)
else:
    print("No transformation matrix found")