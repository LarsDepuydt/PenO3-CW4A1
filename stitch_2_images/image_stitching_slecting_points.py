import cv2
import numpy as np
from matplotlib import pyplot as plt

def harris(img_dir):
    img = cv2.imread(img_dir)
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)  # Turn image to gray

    harris = cv2.cornerHarris(gray,2,3,0.04)  # Applies harris corner detector to gray image

    # Result is dilated for marking the corners, not important
    harris = cv2.dilate(harris,None)

    # Threshold for an optimal value, it may vary depending on the image.
    img[harris>0.01*harris.max()]=[0,0,255]

    plt.figure("Harris detector")
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)), plt.title("Harris")
    plt.xticks([]), plt.yticks([])
    plt.savefig('Harris_detector', bbox_inches='tight')
    plt.show()

harris("../mergeImages/mergePart1.jpg")  # Change this path to one that will lead to your image

