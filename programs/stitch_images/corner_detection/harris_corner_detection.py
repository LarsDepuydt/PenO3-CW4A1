import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt

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
    plt.savefig('../mergeImages/Harris_detector', bbox_inches='tight')
    plt.show()

harris("../mergeImages/mergePart1.jpg")  # Change this path to one that will lead to your image
