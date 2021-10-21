import time
from imutils.video import VideoStream
import imagezmq
import cv2
import numpy as np
from threading import *
import socket
#import pyzmq


PC_IPs = {'whatever': 'tcp://169.254.165.116:5555'}
RB_MAIN_IP = "tcp://mainraspberry:5555"
PC_IP = PC_IPs['whatever']

#
# VOERT EEN KEER UIT
#

'''
Check if leaving videostream on affects performance
'''

# stuurt rechterfoto
picam = VideoStream(usePiCamera=True).start()
time.sleep(2.0)  # allow camera sensor to warm up
imageright = picam.read()
sender = imagezmq.ImageSender(connect_to=RB_MAIN_IP) 
sender.send_image(RB_MAIN_IP, imageright)




# ontvangt matrix
image_hub = imagezmq.ImageHub()
M = image_hub.recv_image()[1]
image_hub.send_reply(b'OK')
print(M)

#
# HERHAALT
#

# maakt linkerfoto
imageleft = picam.read()

# stuurt foto naar andere pi
sender.send_image(RB_MAIN_IP, imageleft)