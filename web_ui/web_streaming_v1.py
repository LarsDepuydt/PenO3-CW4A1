import cv2
import time
import imagezmq
import flask
from flask import request
import numpy as np

# REFERENCE: https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/
# REFERENCE: https://towardsdatascience.com/video-streaming-in-web-browsers-with-opencv-flask-93a38846fe00

first = True
zoom = 0
origin = [0, 0]
h, w = 480, 640
SOURCE = 3
# 1: cv2.VideoCapture, 2: imutils.VideoStream, 3: imagezmq.imagehub
LOG_FPS = False
INIT_PIs = True

def initialize():
    global camera
    if INIT_PIs:
        print("Initing pis")
        from os import path
        from subprocess import run
        PROG_DIR =  str(str(path.dirname(path.realpath(__file__)))[:-6] + "programs/non_multi_threaded").replace("\\", "/")
        REMOTE_EXEC_SCRIPT_PATH = PROG_DIR + "/ssh_conn_exec_cmdfile_win.bat"
        MAIN_CMD_FILE = PROG_DIR + "/main_init.txt"
        HELPER_CMD_FILE = PROG_DIR + "/helper_init.txt"
        run([REMOTE_EXEC_SCRIPT_PATH, "169.254.222.67", MAIN_CMD_FILE])
        run([REMOTE_EXEC_SCRIPT_PATH, "169.254.165.116", HELPER_CMD_FILE])
    if SOURCE == 1:
        camera = cv2.VideoCapture(0)    # laptop webcam
        global w, h
        h, w = camera.read()[1].shape[:2]
    elif SOURCE == 2: 
        import imutils
        vs = imutils.VideoStream(usePiCamera=True).start() # pi camera
        time.sleep(2.0)
    elif SOURCE == 3:
        # DO NOT OPEN IMAGEHUB BEFORE app.run'ning flask!
        global IMAGE_HUB
        IMAGE_HUB = imagezmq.ImageHub()#open_port='tcp://:5555')
    else:
        assert False

def terminate():
    from os import path
    from subprocess import run
    PROG_DIR =  str(str(path.dirname(path.realpath(__file__)))[:-6] + "programs/non_multi_threaded").replace("\\", "/")
    REMOTE_EXEC_SCRIPT_PATH = PROG_DIR + "/ssh_conn_exec_cmdfile_win.bat"
    MAIN_CMD_FILE = PROG_DIR + "/main_terminate.txt"
    HELPER_CMD_FILE = PROG_DIR + "/helper_terminate.txt"
    run([REMOTE_EXEC_SCRIPT_PATH, "169.254.165.116", MAIN_CMD_FILE])
    run([REMOTE_EXEC_SCRIPT_PATH, "169.254.222.67", HELPER_CMD_FILE])

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
    global HEIGHT, WIDTH, h, w
    HEIGHT, WIDTH = camera.read()[1].shape[:2]
    while True:
        succes, frame = camera.read()
        # test zoom
        frame = frame[origin[1]:origin[1] + h, origin[0]:origin[0] + w]
        if not succes:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def gen_frames_imagehub(first=True):
    global HEIGHT, WIDTH, h, w
    if first:
        HEIGHT, WIDTH = IMAGE_HUB.recv_image()[1].shape[:2]
        print("In FIRST IN GEN_FRAMES")
    while True:
        frame = IMAGE_HUB.recv_image()[1][origin[1]:origin[1] + h, origin[0]:origin[0] + w]
        IMAGE_HUB.send_reply(b'OK')
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', frame)[1].tobytes() + b'\r\n')

def gen_frames_imagehub_log_fps():
    img_hub_fps, web_app_fps, t_old = [], [], 0
    IMAGE_HUB = imagezmq.ImageHub()#open_port='tcp://:5555')
    while True:
        frame = IMAGE_HUB.recv_image()[1]
        IMAGE_HUB.send_reply(b'OK')
        t_after_image = time.perf_counter()
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


@app.route('/', methods=['POST', 'GET'])
def index():
    global zoom, h, w, origin, first
    print("beginning index() - first=", first)
    if request.method == 'POST':
        if request.form['button'] == 'terminate':
            print("TERMINATE button clicked")
            first = True
            terminate()
        elif request.form['button'] == 'restart':
            print("RESTART button clicked")
            first = True
            print('restarting - first=', first)
            terminate()
            initialize()
        elif request.form['button'] == 'calibrate':
            print("CALIBRATION button clicked")
        elif request.form['button'] == 'loadpreset':
            print('LOAD PRESET button clicked')
        elif request.form['button'] == 'fullview':
            zoom = 0
            w = WIDTH
            h = HEIGHT
            origin = [0, 0]
            print('FULL VIEW button clicked')
        elif request.form['button'] == 'fillview':
            print('FILL VIEW button clicked')
        elif request.form['button'] == 'zoomin':
            if zoom < 0.4: # crash otherwise
                zoom += 0.05
                zoom = round(zoom, 2)
                w = int(WIDTH*(1-2*zoom))
                h = int(HEIGHT*(1-2*zoom))
                origin = [int(WIDTH*zoom), int(HEIGHT*zoom)]
            print("ZOOM IN button clicked")
            print(zoom)
        elif request.form['button'] == 'zoomout':
            if zoom > 0.05:
                zoom -= 0.05
                zoom = round(zoom, 2)
            elif zoom > 0:
                zoom = 0
            origin = [int(WIDTH*zoom), int(HEIGHT*zoom)]
            w = int(WIDTH*(1-2*zoom))
            h = int(HEIGHT*(1-2*zoom))
            print('ZOOM OUT button clicked')
        elif request.form['button'] == 'panleft':
            if origin[0] > int(w*0.05):
                origin[0] -= int(w*0.05)
            elif origin[0] > 0:
                origin[0] = 0
            print('PAN LEFT button clicked')
        elif request.form['button'] == 'panright':
            if origin[0] + w + int(w*0.05) < WIDTH:
                origin[0] += int(w*0.05)
            elif origin[0] + w < WIDTH:
                origin[0] = WIDTH - w
            print('PAN RIGHT button clicked')
        elif request.form['button'] == 'panup':
            if origin[1] > int(h*0.05):
                origin[1] -= int(h*0.05)
            elif origin[1] > 0:
                origin[1] = 0
            print('PAN UP button clicked')
        elif request.form['button'] == 'pandown':
            if origin[1] + h + int(h*0.05) < HEIGHT:
                origin[1] += int(h*0.05)
            elif origin[1] + h < HEIGHT:
                origin[1] = HEIGHT - h
            print('PAN DOWN button clicked')
        else:
            print("UNKNOWN POST REQUEST")
    else:
        print("NON-POST REQUEST")
        pass
    print("RETURNING render_template(index.html), first=", first)
    return flask.render_template('index.html')


if SOURCE == 1 or SOURCE == 2:
    if LOG_FPS:
        @app.route('/video_feed')
        def video_feed():
            return flask.Response(gen_frames_cv2_videoCapture_log_fps(), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        @app.route('/video_feed')
        def video_feed():
            return flask.Response(gen_frames_cv2_videocapture(), mimetype='multipart/x-mixed-replace; boundary=frame')
elif SOURCE == 3:
    if LOG_FPS: 
        @app.route('/video_feed')
        def video_feed():
            return flask.Response(gen_frames_imagehub_log_fps(), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        @app.route('/video_feed')
        def video_feed():
            return flask.Response(gen_frames_imagehub(first), mimetype='multipart/x-mixed-replace; boundary=frame')
        first = False



if __name__ == "__main__":
    app.run(debug=True)
    