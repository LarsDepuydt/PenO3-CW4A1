from picamera import PiCamera
from time import sleep

camera = PiCamera()
camera.start_preview()
for i in range(20):
    sleep(1.0)
    camera.capture('./foto'+str(i)+'.jpg')
sleep(1.0)
camera.stop_preview()