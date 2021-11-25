import cv2
import time
import imagezmq
import flask
from flask import request

# REFERENCE: https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/
# REFERENCE: https://towardsdatascience.com/video-streaming-in-web-browsers-with-opencv-flask-93a38846fe00

MODE = 1
TRYME = 1

import os
PROG_DIR =  str(str(os.path.dirname(os.path.realpath(__file__)))[:-6] + "programs/MAIN_code/non_multi_threaded").replace("\\", "/")
INIT_MAIN_CMD = PROG_DIR + "/ssh_conn_and_execute_cmd_win.bat"
MAIN_CMD_FILE = PROG_DIR + "/main_init.txt"
import subprocess
subprocess.run([INIT_MAIN_CMD, "169.254.222.67", MAIN_CMD_FILE])
# 1:  cv2.VideoCapture
# 2: imutils.VideoStream(usePiCamera=True)
# 3: imagezmq.ImageHub
# 4: imagezmq.ImageHub  (log fps)

if MODE == 1 or MODE == 2:
    camera = cv2.VideoCapture(0)    # laptop webcam
    pass
elif MODE == 3: 
    import imutils
    vs = imutils.VideoStream(usePiCamera=True).start() # pi camera
    time.sleep(2.0)
elif MODE == 4 or MODE == 5:
    # DO NOT OPEN IMAGEHUB BEFORE app.run'ning flask!  
    pass

app = flask.Flask(__name__)

# Show camera feed troubleshooting code
'''
    # Troubleshoot camera: show camera feed
    while True:
        check, frame = cam.read()
        #cv2.imshow('video', frame)
        key = cv2.waitKey(1)
        if key == 27:
            break
    cam.release()
    cv2.destroyAllWindows()
    '''

def gen_frames_cv2_videoCapture_log_fps():
    frames_per_second, t_old = [], 0
    while True:
        t = time.perf_counter
        succes, frame = camera.read()
        if not succes:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        t = time.perf_counter()
        frames_per_second.append(1/(t-t_old))
        t_old = t
        if len(frames_per_second) == 10:
            print(sum(frames_per_second)/10)
            frames_per_second = []

def gen_frames_cv2_videocapture():
    while True:
        succes, frame = camera.read()
        if not succes:
            break
        else:
            if TRYME:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                print("HOHOHOHO")

def gen_frames_imagehub():
    IMAGE_HUB = imagezmq.ImageHub()#open_port='tcp://:5555')
    while True:
        frame = IMAGE_HUB.recv_image()[1]
        IMAGE_HUB.send_reply(b'OK')
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', frame)[1].tobytes() + b'\r\n')

def gen_frames_imagehub_log_fps():
    img_hub_fps, web_app_fps, t_old = [], [], 0
    IMAGE_HUB = imagezmq.ImageHub()#open_port='tcp://:5555')
    while True:
        frame = IMAGE_HUB.recv_image()[1]
        IMAGE_HUB.send_reply(b'OK')
        t_after_image = time.perf_counter()
        '''
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')'''
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', frame)[1].tobytes() + b'\r\n')
        
        t_after_yield = time.perf_counter()
        web_app_fps.append(1/(t_after_yield - t_after_image))
        img_hub_fps.append(1/(t_after_image - t_old))
        t_old = t_after_yield

        if len(web_app_fps) == 10:
            print("Webapp    fps 10avg  : ", sum(web_app_fps)/10)
            print("Webapp fps 1sample: ", web_app_fps[-1])
            print("Imagehub  fps 10avg  : ", sum(img_hub_fps)/10)
            print("Imagehub fps 1sample: ", img_hub_fps[-1])
            web_app_fps, img_hub_fps = [], []

@app.route('/hello')
def hello():
    return 'Hello, World'

# @app.route('/')
# def index():
#     return flask.render_template('index.html')

@app.route('/', methods=['POST', 'GET'])
def index():
    error = None
    if request.method == 'POST':
        if request.form['button'] == 'start':
            print("START button clicked")
        elif request.form['button'] == 'stop':
            print("STOP button clicked")
        elif request.form['button'] == 'calibrate':
            print("CALIBRATION button clicked")
        elif request.form['button'] == 'loadpreset':
            print('LOADPRESET button clicked')
        else:
            print("UNKNOWN POST REQUEST")
    else:
        print("YOOOO")
        pass
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return flask.render_template('index.html', error=error)


if MODE == 1:
    @app.route('/video_feed')
    def video_feed():
        return flask.Response(gen_frames_cv2_videocapture(), mimetype='multipart/x-mixed-replace; boundary=frame')
elif MODE == 2:
    def video_feed():
        return flask.Response(gen_frames_cv2_videoCapture_log_fps(), mimetype='multipart/x-mixed-replace; boundary=frame')
elif MODE == 3:
    pass
elif MODE == 4:
    @app.route('/video_feed')
    def video_feed():
        return flask.Response(gen_frames_imagehub(), mimetype='multipart/x-mixed-replace; boundary=frame')
elif MODE == 5:
    @app.route('/video_feed')
    def video_feed():
        return flask.Response(gen_frames_imagehub_log_fps(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True)