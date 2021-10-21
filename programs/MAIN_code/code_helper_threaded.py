from imutils.video import VideoStream
import imagezmq
import cv2
import numpy as np
import threading
from time import sleep

RB_IP_MAIN = ""
#
# One time only
#

# Sends left image
picam = VideoStream(usePiCamera=True).start()
imageright = picam.read()
sender = imagezmq.ImageSender(connect_to='tcp://Laptop-Wout:5555')  # Input pc-ip (possibly webserver to sent to)
rb_name = RB_IP_MAIN  # send RPi hostname with each image
sender.send_image(rb_name, imageright)

# Receives matrix
M = []

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
        while True:
            picam = VideoStream(usePiCamera=True).start()
            self.lijst[0] = picam.read()


class TransformImage(threading.Thread):
    def __init__(self, lijst, H):
        super().__init__()
        self.img1 = lijst[0]
        self.lijst = lijst
        self.H = H

    def run(self):
        while True:
            if self.img1 is not None:
                rows1, cols1 = self.img1.shape[:2]
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

                self.lijst[1] = cv2.warpPerspective(self.img1, H_translation.dot(self.H), (x_max - x_min, y_max - y_min))


class SendImageToMain(threading.Thread):
    def __init__(self, lijst):
        super().__init__()
        self.lijst = lijst

    def run(self):
        while True:
            sender = imagezmq.ImageSender(connect_to='tcp://Laptop-Wout:5555')  # Input pc-ip (possibly webserver)
            rpi_name = ""
            sender.send_image(rpi_name, self.lijst[1])


step_1 = TakeLeftImage(image_list)
step_2 = TransformImage(image_list, M)
step_3 = SendImageToMain(image_list)

step_1.start()
sleep(0.001)
step_2.start()
sleep(0.001)
step_3.start()
