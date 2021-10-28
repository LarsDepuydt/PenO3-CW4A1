import zmq

RB_HELPER_IP  = "tcp://helperraspberry:5000"
RB_MAIN_IP    = "tcp://mainraspberry:5000"

image_hub = imagezmq.ImageHub()
imageleft = image_hub.recv_image()[1]
image_hub.send_reply(b'OK')

print(imageleft)
print("DONE")
