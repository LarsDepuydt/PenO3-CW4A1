import cv2
import imagezmq

  # Instantiate and provide the first sender / publisher address
image_hub = imagezmq.ImageHub(open_port='tcp://192.168.137.56:5555', REQ_REP=False)
image_hub.connect('tcp://192.168.137.56:5555')
# image_hub.connect('tcp://192.168.0.102:5555')  # must specify address for every sender
# image_hub.connect('tcp://192.168.0.103:5555')  # repeat as needed

while True:
 rpi_name, image = image_hub.recv_image()
 cv2.imshow(rpi_name, image) # 1 window for each unique RPi name
 cv2.waitKey(1)