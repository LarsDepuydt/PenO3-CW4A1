import cv2 as cv
from matplotlib import pyplot as plt
import time
t_start = time.perf_counter()

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
    plt.savefig('../../../images/testing_images_online/corners/harris_detector_pi.jpg', bbox_inches='tight')

harris("../../../images/testing_images_pi/lokaal/image_for_testing_1.jpg")  # Change this path to one that will lead to your image
print(time.perf_counter() - t_start)
print("done")
