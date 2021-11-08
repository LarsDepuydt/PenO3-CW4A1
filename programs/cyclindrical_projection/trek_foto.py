from picamera import PiCamera
from time import sleep

camera = PiCamera()
camera.start_preview()
sleep(4.0)
camera.capture('./foto10.jpg')
sleep(1.0)
camera.stop_preview()