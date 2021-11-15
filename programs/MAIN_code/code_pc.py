import imagezmq
import cv2

image_hub = imagezmq.ImageHub()
# ontvangt foto's
while True:

    rpi_name, image = image_hub.recv_image()
    cv2.imshow(rpi_name, image)  # 1 window for each RPi
    image_hub.send_reply(b'OK')
    if cv2.waitKey(1) == 27:
        cv2.destroyAllWindows
        break
    print('here')