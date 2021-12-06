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
<<<<<<< HEAD
    t = time.perf_counter()
    f.append(1/(t-t_old))
    t_old = t
    #print(f)
    







=======
>>>>>>> c9e05af3c5629ad329bfd32f1aaa581ded73196a



