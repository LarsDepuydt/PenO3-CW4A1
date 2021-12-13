import imagezmq
import cv2
import time

# ontvangt foto's

IMAGE_HUB = imagezmq.ImageHub()
while True:
    rpi_name, image = IMAGE_HUB.recv_image()
    cv2.imshow(rpi_name, image)  # 1 window for each RPi
    cv2.waitKey(1)
    IMAGE_HUB.send_reply(b'OK')
    










