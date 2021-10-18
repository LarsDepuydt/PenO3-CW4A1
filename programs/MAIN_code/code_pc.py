import imagezmq
import cv2

# ontvangt foto's
while True:
    image_hub = imagezmq.ImageHub()
    rpi_name, image = image_hub.recv_image()
    cv2.imshow(rpi_name, image)  # 1 window for each RPi
    cv2.waitKey(1)
    image_hub.send_reply(b'OK')