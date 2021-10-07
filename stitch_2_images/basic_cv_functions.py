import cv2
import numpy as np

img = cv2.imread("../mergeImages/lena.png")
kernel = np.ones((5, 5), np.uint8)


imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
imgBlur = cv2.GaussianBlur(imgGray, (7, 7), 0)
imgCanny = cv2.Canny(img, 150, 200)
imgDialation = cv2.dilate(imgCanny, kernel, iterations=1)
imgEroded = cv2.erode(imgDialation, kernel, iterations=1)

cv2.imshow("Gray Image", imgGray)
cv2.imshow("Blur Image", imgBlur)
cv2.imshow("Canny Image", imgCanny)
cv2.imshow("Dialation Image", imgDialation)
cv2.imshow("Eroded Image", imgEroded)

cv2.imwrite("../mergeImages/basic_editing/imgGray.jpg", imgGray)
cv2.imwrite("../mergeImages/basic_editing/imgBlur.jpg", imgBlur)
cv2.imwrite("../mergeImages/basic_editing/imgCanny.jpg", imgCanny)
cv2.imwrite("../mergeImages/basic_editing/imgDialation.jpg", imgDialation)
cv2.imwrite("../mergeImages/basic_editing/imgEroded.jpg", imgEroded)

print("done")
cv2.waitKey(0)