from re import I
import cv2
import time
import imagezmq
import flask
from flask import request
import numpy as np

# REFERENCE: https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/
# REFERENCE: https://towardsdatascience.com/video-streaming-in-web-browsers-with-opencv-flask-93a38846fe00

# ==============================
# CONSTANTS
# ==============================

RUNNING = False
LOG_FPS = False
DEBUG = True
first = True

image_hub = -1
running = False
resolution = [320, 240]
blend_frac = 0.5
x_t = 0
calibrate = False

frame_width, frame_height = 1000, 240 # placeholder for frame_width and frame_height
fill_height = int(0.9*frame_height)
w, h = frame_width, frame_height # shown frame width (for zooming)
zoom = 0
origin = [0, 0]

MAIN_INIT_CMDS = [
    'echo "On the main pi, initting main"',
    'cd Desktop/PenO3-CW4A1/programs/non_multi_threaded',
    'python3 main_v9.py']

HELPER_INIT_CMDS = [
    'echo "On the helper pi, initting helper"', 
    'cd Desktop/PenO3-CW4A1/venv/bin',
    'source activate',
    'cd ../../programs/non_multi_threaded',
    'python3 helper_v9.py']

MAIN_TERM_CMDS = [
    'echo "IN MAIN PI: terminating all python"'
    'sudo pkill python']

HELPER_TERM_CMDS = [
    'echo "IN HELPER PI: terminating all python"'
    'sudo pkill python']

def get_pc_ip():
    # REFERENCE: https://stackoverflow.com/a/59004409
    import subprocess
    out = str(subprocess.run("for /f \"tokens=3 delims=: \" %i  in ('netsh interface ip show config name^=\"Ethernet\" ^| findstr \"IP Address\"') do echo %i", shell=True, capture_output=True).stdout)
    i1 = out.find("echo") + 5 # deletes "echo " 
    i2 = i1 + out[i1:].find("\\r") - 1 # deletes " "
    return out[i1:i2]

PC_IP = get_pc_ip()
PC_IP = "169.254.236.78"
MAIN_PI_IP = "169.254.165.116"
HELPER_PI_IP = "169.254.222.67"

# ==============================
# FUNCTIONS
# ==============================

def initialize():
    print("Initing pis")
    from os import path
    from subprocess import run
    PROG_DIR =  str(str(path.dirname(path.realpath(__file__)))[:-6] + "programs/non_multi_threaded").replace("\\", "/")
    REMOTE_EXEC_SCRIPT_PATH = PROG_DIR + "/ssh_conn_exec_cmdfile_win.bat"
    MAIN_CMD_FILE_PATH = PROG_DIR + "/main_init.txt"
    HELPER_CMD_FILE = PROG_DIR + "/helper_init.txt"
    run([REMOTE_EXEC_SCRIPT_PATH, "169.254.165.116", MAIN_CMD_FILE_PATH])
    run([REMOTE_EXEC_SCRIPT_PATH, "169.254.222.67", HELPER_CMD_FILE])

def terminate():
    from os import path
    from subprocess import run
    PROG_DIR =  str(str(path.dirname(path.realpath(__file__)))[:-6] + "programs/non_multi_threaded").replace("\\", "/")
    REMOTE_EXEC_SCRIPT_PATH = PROG_DIR + "/ssh_conn_exec_cmdfile_win.bat"
    MAIN_CMD_FILE_PATH = PROG_DIR + "/main_terminate.txt"
    HELPER_CMD_FILE = PROG_DIR + "/helper_terminate.txt"
    run([REMOTE_EXEC_SCRIPT_PATH, "169.254.165.116", MAIN_CMD_FILE_PATH])
    run([REMOTE_EXEC_SCRIPT_PATH, "169.254.222.67", HELPER_CMD_FILE])

def gen_command_files(maincmds, helpercmds, use_keypnt, res, blend_frac, x_t, pc_ip):
    import os.path
    CURRENT_DIR = str(os.path.dirname(os.path.realpath(__file__))).replace("\\", "/")
    DIRS = CURRENT_DIR.split("/")
    for i, s in enumerate(DIRS):
        if s == "PenO3-CW4A1":
            REPO_ROOT = "/".join(DIRS[:i+1])
    CMD_FILE_SAVE_DIR = REPO_ROOT + "/programs/non_multi_threaded/"
    print("Saving command files to: ", CMD_FILE_SAVE_DIR)

    sp = '" "'
    argstr = ' "' +  str(use_keypnt) + sp + str(res[0])+","+str(res[1]) + sp + str(blend_frac) + sp + str(x_t) + sp + pc_ip + '"'
    print("ARGSTR", argstr)

    open(CMD_FILE_SAVE_DIR + 'main_init.txt', 'w').close()
    open(CMD_FILE_SAVE_DIR + 'helper_init.txt', 'w').close()

    maincmds = maincmds[:] # copy so it doesn't edit the global variable
    maincmds[-1] += argstr
    maincmds = [x+'\n' for x in maincmds]
    maincmds.append("sleep 5")
    with open(CMD_FILE_SAVE_DIR + 'main_init.txt', mode='w') as f:
        f.writelines(maincmds)

    helpercmds = helpercmds[:]
    helpercmds[-1] += argstr
    helpercmds = [x + '\n' for x in helpercmds]
    helpercmds.append("sleep 5")
    with open(CMD_FILE_SAVE_DIR + 'helper_init.txt', mode='w') as f:
        f.writelines(helpercmds)

def gen_frames_imagehub():
    global zoom, h, w, frame_width, frame_height, origin, image_hub, fill_height
    if image_hub != -1:
        image_hub.close()
    print("(Re)starting ImageHub")
    image_hub = imagezmq.ImageHub()
    img = image_hub.recv_image()[1]
    image_hub.send_reply(b'OK')
    frame_height, frame_width = img.shape[:2]
    for i, r in img:
        if i < frame_height/2:
            if r[0] == np.array([0, 0, 0]):
                fill_height = i + 1
    while True:
        frame = image_hub.recv_image()[1][origin[1]:origin[1] + h, origin[0]:origin[0] + w]
        image_hub.send_reply(b'OK')
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', frame)[1].tobytes() + b'\r\n')

def gen_frames_imagehub_log_fps():
    global zoom, h, w, frame_width, frame_height, origin, image_hub, fill_height
    img_hub_fps, web_app_fps, t_old = [], [], 0
    if image_hub != -1:
        image_hub.close()
    print("(Re)starting ImageHub")
    image_hub = imagezmq.ImageHub()
    img = image_hub.recv_image()[1]
    image_hub.send_reply(b'OK')
    frame_height, frame_width = img.shape[:2]
    for i, r in img:
        if i < frame_height/2:
            if r[0] == np.array([0, 0, 0]):
                fill_height = i + 1
    while True:
        frame = image_hub.recv_image()[1][origin[1]:origin[1] + h, origin[0]:origin[0] + w]
        image_hub.send_reply(b'OK')
        t_after_image = time.perf_counter()
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', frame)[1].tobytes() + b'\r\n')
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', frame)[1].tobytes() + b'\r\n')
        
        t_after_yield = time.perf_counter()
        web_app_fps.append(1/(t_after_yield - t_after_image))
        img_hub_fps.append(1/(t_after_image - t_old))
        t_old = t_after_yield

        if len(web_app_fps) == 50:
            print("Webapp fps 50avg     : ", sum(web_app_fps)/50)
            print("Webapp fps 1sample   : ", web_app_fps[-1])
            print("Imagehub fps 50avg   : ", sum(img_hub_fps)/50)
            print("Imagehub fps 1sample : ", img_hub_fps[-1])
            web_app_fps, img_hub_fps = [], []

def is_port_in_use(port):
    # REFERENCE: https://codereview.stackexchange.com/questions/116450/find-available-ports-on-localhost
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# ==============================
# FLASK
# ==============================

flask.Response()
app = flask.Flask(__name__)

@app.route('/video_feed')
def video_feed():
    return flask.Response(gen_frames_imagehub(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/', methods=['POST', 'GET'])
def index():
    global zoom, h, w, frame_width, frame_height, origin, blend_frac, resolution, first
    if first:
        terminate()
        first = False
    if request.method == 'POST':
        if request.form['button'] == 'poweron':
            print("POWER button clicked: powering on")
            initialize()
        elif request.form['button'] == 'poweroff':
            print("POWER button clicked: powering off")
            terminate()
        elif request.form['button'] == 'calibrate':
            print("CALIBRATION button clicked")
            terminate()
            gen_command_files(MAIN_INIT_CMDS, HELPER_INIT_CMDS, 1, resolution, blend_frac, 0, PC_IP)
            initialize()
        elif request.form['button'] == 'set180':
            print("SETTO180 button clicked")
            terminate()
            # x_t = int(0.8 * resolution[0])
            x_t = 244
            gen_command_files(MAIN_INIT_CMDS, HELPER_INIT_CMDS, 0, resolution, blend_frac, x_t, PC_IP)
            initialize()
        elif request.form['button'] == 'setto270':
            print("SETTO270 button clicked")
            terminate()
            # x_t = int(0.08 * resolution[0])
            x_t = 28
            gen_command_files(MAIN_INIT_CMDS, HELPER_INIT_CMDS, 0, resolution, blend_frac, x_t, PC_IP)
            initialize()
        elif request.form['button'] == 'decreaseblendfrac':
            print("Decreasing blend frac...")
            if blend_frac > 0.1:
                blend_frac = round(blend_frac-0.1, 1)
            if blend_frac <= 0.1:
                blend_frac = 0
        elif request.form['button'] == 'increaseblendfrac':
            print("Increasing blend frac...")
            if blend_frac < 0.9:
                blend_frac = round(blend_frac+0.1, 1)
            if blend_frac >= 0.9:
                blend_frac = 1
        elif request.form['button'] == 'fullview':
            print('FULL VIEW button clicked')
            zoom = 0
            w = frame_width
            h = frame_height
            origin = [0, 0]
        elif request.form['button'] == 'fillview':
            print('FILL VIEW button clicked')
            zoom = 0
            origin = [0, 0]
            w = frame_width
            h = fill_height
        elif request.form['button'] == 'zoomin':
            if zoom < 0.4: # crash if allow higher zoom
                zoom += 0.05
                zoom = round(zoom, 2)
                w = int(frame_width*(1-2*zoom))
                h = int(frame_height*(1-2*zoom))
                origin = [int(frame_width*zoom), int(frame_height*zoom)]
            print("ZOOM IN button clicked")
            print(zoom)
        elif request.form['button'] == 'zoomout':
            if zoom > 0.05:
                zoom -= 0.05
                zoom = round(zoom, 2)
            elif zoom > 0:
                zoom = 0
            origin = [int(frame_width*zoom), int(frame_height*zoom)]
            w = int(frame_width*(1-2*zoom))
            h = int(frame_height*(1-2*zoom))
            print('ZOOM OUT button clicked')
        elif request.form['button'] == 'panleft':
            if origin[0] > int(w*0.05):
                origin[0] -= int(w*0.05)
            elif origin[0] > 0:
                origin[0] = 0
            print('PAN LEFT button clicked')
        elif request.form['button'] == 'panright':
            if origin[0] + w + int(w*0.05) < frame_width:
                origin[0] += int(w*0.05)
            elif origin[0] + w < frame_width:
                origin[0] = frame_width - w
            print('PAN RIGHT button clicked')
        elif request.form['button'] == 'panup':
            if origin[1] > int(h*0.05):
                origin[1] -= int(h*0.05)
            elif origin[1] > 0:
                origin[1] = 0
            print('PAN UP button clicked')
        elif request.form['button'] == 'pandown':
            if origin[1] + h + int(h*0.05) < frame_height:
                origin[1] += int(h*0.05)
            elif origin[1] + h < frame_height:
                origin[1] = frame_height - h
            print('PAN DOWN button clicked')
        else:
            print("UNKNOWN POST REQUEST")
    else:
        print("NON-POST REQUEST")
        pass
    return flask.render_template('index.html', blend_frac=blend_frac)


if False:
    @app.route('/video_feed')
    def video_feed():
        return flask.Response(gen_frames_imagehub_log_fps(), mimetype='multipart/x-mixed-replace; boundary=frame')
elif False:
    @app.route('/video_feed')
    def video_feed():
        return flask.Response(gen_frames_imagehub(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=DEBUG)
