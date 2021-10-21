#import pyzmq
import numpy
import imagezmq


RB_MAIN_IP = "tcp://mainraspberry:5555"
RB_HELPER_IP = "tcp://helperraspberry:5555"

image_hub = imagezmq.ImageHub()

rpi_name, recmatrix = image_hub.recv_image()
image_hub.send_reply(b'OK')
print(recmatrix)
print(type(recmatrix))
