from imutils.video import VideoStream
from picamera import PiCamera
import imagezmq
import cv2
import numpy as np
import threading
from time import sleep

RB_IP_MAIN = "tcp://192.168.137.1:5555"
RESOLUTION = (640, 640)


picam = VideoStream(usePiCamera=True, resolution=RESOLUTION).start()
#cam.resolution(640, 480)
sleep(2.0)  # allow camera sensor to warm up
sender = imagezmq.ImageSender(connect_to=RB_IP_MAIN)  # Input pc-ip (possibly webserver to sent to)
while True:
    sender.send_image(RB_IP_MAIN, picam.read())