import cv2
import numpy as np
img1 = cv2.imread("cylindrical_projection_images\left0_cyl.png")
img2 = cv2.imread("cylindrical_projection_images/right0_cyl.png")

vis = np.concatenate((img1[:, 0:437], img2[:, 70:]), axis=1)
cv2.imwrite('out.png', vis)