import zmq

RB_HELPER_IP  = "tcp://helperraspberry:5000"
RB_MAIN_IP    = "tcp://mainraspberry:5000"

image_hub = imagezmq.ImageHub()
sender = imagezmq.ImageSender(connect_to=RB_HELPER_IP)
sender.send_image(RB_MAIN_IP, "ready"))

print("DONE")
