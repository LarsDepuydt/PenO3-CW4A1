import cv2
import numpy as np

img1 = cv2.imread('/Users/lars/Desktop/PenO3-CW4A1/programs/cylindrical_projection/cylindrical_projection_images/left0_cyl.png')
img2 = cv2.imread('/Users/lars/Desktop/PenO3-CW4A1/programs/cylindrical_projection/cylindrical_projection_images/right0_cyl.png')

# Store height and width of the image
height, width = img1.shape[:2]

quarter_height, quarter_width = height / 4, width / 4

T1 = np.float32([[1, 0, width], [0, 1, 0]])
T2 = np.float32([[1, 0, 0], [0, 1, 0]])

# We use warpAffine to transform
# the image using the matrix, T
img2_translation = cv2.warpAffine(img1, T1, (width*2, height))

cv2.imshow('Translation', img2_translation)
cv2.waitKey()

cv2.destroyAllWindows()