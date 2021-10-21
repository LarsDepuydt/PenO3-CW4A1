#import pyzmq
import numpy
import imagezmq


RB_HELPER_IP = "tcp://helperraspberry:5555"
RB_MAIN_IP = "tcp://mainraspberry:5555"


M = numpy.array([[1, 2, 3],
           [4, 5, 6]])

sender = imagezmq.ImageSender(connect_to=RB_HELPER_IP)
sender.send_image(RB_MAIN_IP, M)
          



          

          