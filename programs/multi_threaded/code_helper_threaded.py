from imutils.video import VideoStream
from picamera import PiCamera
import imagezmq
import cv2
import numpy as np
import threading
from time import sleep

ETHERNET = 'tcp://169.254.222.67:5555'
RB_IP_MAIN = ETHERNET
ETHERNET2 = 'tcp://169.254.165.116:5555'
RB_IP_HELPER = ETHERNET2
# RB_IP_MAIN = "tcp://mainraspberry:5555"
#
# One time only
#

# Sends left image
# cam = PiCamera()
picam = VideoStream(usePiCamera=True).start()
# cam.resolution(640, 480)
sleep(2.0)  # allow camera sensor to warm up
imageright = picam.read()
sender = imagezmq.ImageSender(connect_to=RB_IP_MAIN)  # Input pc-ip (possibly webserver to sent to)
sender.send_image(RB_IP_MAIN, imageright)

# Receives matrix
image_hub = imagezmq.ImageHub()
M = image_hub.recv_image()[1]
image_hub.send_reply(b'OK')
print(M)



#
# Repeating
#
left_image = None
output_image = None
image_list = [left_image, output_image]


class TakeLeftImage(threading.Thread):
    def __init__(self, lijst):
        super().__init__()
        self.lijst = lijst

    def run(self):
        print("take image class")
        while True:
            self.lijst[0] = picam.read()


class TransformImage(threading.Thread):
    def __init__(self, img1, lijst, H):
        super().__init__()
        self.img1 = img1
        self.lijst = lijst
        self.H = H
        print(type(img1))
        print(type(self.img1))

    def run(self):
        global image_list
        img1 = image_list[0]
        while True:
            if img1 is not None:
                print("erin transform")
                rows1, cols1 = img1.shape[:2]
                list_of_points_1 = np.float32([[0, 0], [0, rows1], [cols1, rows1], [cols1, 0]]).reshape(-1, 1, 2)
                temp_points = np.float32([[0, 0], [0, rows1], [cols1, rows1], [cols1, 0]]).reshape(-1, 1, 2)

                # When we have established a homography we need to warp perspective
                # Change field of view
                list_of_points_2 = cv2.perspectiveTransform(temp_points, self.H)

                list_of_points = np.concatenate((list_of_points_1, list_of_points_2), axis=0)

                [x_min, y_min] = np.int32(list_of_points.min(axis=0).ravel() - 0.5)
                [x_max, y_max] = np.int32(list_of_points.max(axis=0).ravel() + 0.5)

                translation_dist = [-x_min, -y_min]

                H_translation = np.array([[1, 0, translation_dist[0]], [0, 1, translation_dist[1]], [0, 0, 1]])

                self.lijst[1] = cv2.warpPerspective(img1, H_translation.dot(self.H), (x_max - x_min, y_max - y_min))


class SendImageToMain(threading.Thread):
    def __init__(self, lijst):
        super().__init__()
        self.lijst = lijst

    def run(self):
        while True:
            if self.lijst[1] is not None:
                print("voor error")
                sender.send_image(RB_IP_MAIN, self.lijst[1])


step_1 = TakeLeftImage(image_list)
step_2 = TransformImage(image_list[0], image_list, M)
step_3 = SendImageToMain(image_list)

step_1.start()
sleep(0.001)
step_2.start()
sleep(0.001)
step_3.start()
