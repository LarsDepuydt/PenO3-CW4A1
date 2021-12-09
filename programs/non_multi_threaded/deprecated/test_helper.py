from imutils.video import VideoStream
import imagezmq
import numpy as np
import cv2
from time import sleep
import sys


RESOLUTION = (496, 368)

M = np.array([[3.30856936, -1.790123*0.1, -7.5959407*100],
              [6.5262732*0.1, 3.18974463, -5.69635988*100],
              [1.71384892*0.001, 8.2359673*0.0001, 1]])

PICAM = VideoStream(usePiCamera=True, resolution=RESOLUTION).start()
sleep(2.0)  # allow camera sensor to warm up

imagergb = cv2.imread('image_left.jpg')

print(type(imagergb))
srcpts = np.array([[0, 496], [0, 368], [496, 368], [496, 0]], dtype=np.float32).reshape(-1, 1, 2)
srcpts = srcpts
print(srcpts)
#destpts = np.float32([[0, 200], [600, 0], [0, 700], [1000, 700]])

dstpts = cv2.perspectiveTransform(srcpts, M)


#resmatrix = cv2.getPerspectiveTransform(srcpts, destpts)
print("resmatrix: ", M, type(M))
print("imagergb: ", imagergb, type(imagergb))
resultimage = cv2.warpPerspective(imagergb, M, (500, 600))



while True:
    cv2.imshow('IMAGINATION', imagergb)
    cv2.imshow('RESULT', resultimage)
    if cv2.waitKey(24) == 27:
        break





