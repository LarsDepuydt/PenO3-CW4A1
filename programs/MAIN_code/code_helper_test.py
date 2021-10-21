import time
from imutils.video import VideoStream
import imagezmq
import cv2
import numpy as np
import threading
import socket

RB_IP_MAIN = ""

#
# VOERT EEN KEER UIT
#

# stuurt linkerfoto
picam = VideoStream(usePiCamera=True).start()
imageright = picam.read()
sender = imagezmq.ImageSender(connect_to='tcp://Laptop-Wout:5555')  # Input pc-ip (possibly webserver to sent to)
rb_name = RB_IP_MAIN  # send RPi hostname with each image
sender.send_image(rb_name, imageright)

# ontvangt matrix
M = []

#
# HERHAALT
#

class take_left_image(threading.Thread):
    def run(self):

class transform_image(threading.Thread):
    def run(self):

class send_image_to_main(threading.Thread):
    def run(self):
