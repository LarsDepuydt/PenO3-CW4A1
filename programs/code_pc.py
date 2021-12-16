import imagezmq
import cv2
from time import perf_counter

# ontvangt foto's
t_old = 0
fps = []
IMAGE_HUB = imagezmq.ImageHub()
while True:
    rpi_name, image = IMAGE_HUB.recv_image()
    cv2.imshow(rpi_name, image)  # 1 window for each RPi
    cv2.waitKey(1)
    IMAGE_HUB.send_reply(b'OK')
    t = perf_counter()
    fps.append(1/(t - t_old))
    t_old = t
    if len(fps) == 50:
        print(sum(fps)/50)
        fps = []
    cv2.imwrite("output.jpg", image)
    
    