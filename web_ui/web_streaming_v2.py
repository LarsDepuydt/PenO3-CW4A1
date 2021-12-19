import cv2
import time
import imagezmq
import flask
from flask import request
import numpy as np
from colorama import Fore, Back, Style

# REFERENCE: https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/
# REFERENCE: https://towardsdatascience.com/video-streaming-in-web-browsers-with-opencv-flask-93a38846fe00

# ==============================
# CONSTANTS
# ==============================

RUNNING = False
LOG_FPS = False
DEBUG = True
LOG_COMMANDLINE = False
first = True
reload_video_feed = True

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

from os import path
REPO_ROOT               =  str(path.dirname(path.realpath(__file__)))[:-6].replace("\\", "/")
PROG_DIR                = REPO_ROOT+ "programs/non_multi_threaded"
REMOTE_EXEC_SCRIPT_PATH = PROG_DIR + "/ssh_conn_exec_cmdfile_win.bat"
MAIN_INIT_CMD_FILE_PATH = PROG_DIR + "/main_init.txt"
HELP_INIT_CMD_FILE_PATH = PROG_DIR + "/helper_init.txt"
MAIN_TERM_CMD_FILE_PATH = PROG_DIR + "/main_terminate.txt"
HELP_TERM_CMD_FILE_PATH = PROG_DIR + "/helper_terminate.txt"

MAIN_INIT_CMDS = [
    'echo "On the main pi, initting main"',
    'cd Desktop/PenO3-CW4A1/programs/non_multi_threaded',
    'python3 main_v9.py']

HELP_INIT_CMDS = [
    'echo "On the helper pi, initting helper"', 
    'cd Desktop/PenO3-CW4A1/venv/bin',
    'source activate',
    'cd ../../programs/non_multi_threaded',
    'python3 helper_v9.py']

MAIN_TERM_CMDS = [
    'echo "IN MAIN PI: terminating all python"'
    'sudo pkill python']

HELP_TERM_CMDS = [
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

def log_fun():
    import inspect
    print(Fore.CYAN + "FUNCTION " + Fore.RESET + str(inspect.stack()[1][3]) + "()")

def initialize():
    log_fun()
    global reload_video_feed
    reload_video_feed = True
    from subprocess import check_output # instead of run, because this one doesn't print anything
    check_output([REMOTE_EXEC_SCRIPT_PATH, "169.254.165.116", MAIN_INIT_CMD_FILE_PATH], shell=True)
    check_output([REMOTE_EXEC_SCRIPT_PATH, "169.254.222.67", HELP_INIT_CMD_FILE_PATH])

def terminate():
    log_fun()
    from time import sleep
    from subprocess import check_output # instead of run because this one doesn't print anything
    global running, reload_video_feed

    reload_video_feed = False
    # wait until gen_frames_imagehub() has gone out of loop and closed imagehub: 
    running = False
    while True:             
        if image_hub == -1:
            break
        else:
            sleep(0.5)

    check_output([REMOTE_EXEC_SCRIPT_PATH, "169.254.165.116", MAIN_TERM_CMD_FILE_PATH])
    check_output([REMOTE_EXEC_SCRIPT_PATH, "169.254.222.67",  HELP_TERM_CMD_FILE_PATH])

def gen_init_cmd_files(maincmds, helpercmds, use_keypnt, res, blend_frac, x_t, pc_ip):
    log_fun()
    import os.path
    CURRENT_DIR = str(os.path.dirname(os.path.realpath(__file__))).replace("\\", "/")
    DIRS = CURRENT_DIR.split("/")
    for i, s in enumerate(DIRS):
        if s == "PenO3-CW4A1":
            REPO_ROOT = "/".join(DIRS[:i+1])
    CMD_FILE_SAVE_DIR = REPO_ROOT + "/programs/non_multi_threaded/"
    # print("Saving command files to: ", CMD_FILE_SAVE_DIR)

    sp = '" "'
    argstr = ' "' +  str(use_keypnt) + sp + str(res[0])+","+str(res[1]) + sp + str(blend_frac) + sp + str(x_t) + sp + pc_ip + '"'
    # print("ARGSTR", argstr)

    maincmds = maincmds[:] # copy so it doesn't edit the global variable
    maincmds[-1] += argstr
    maincmds = [x+'\n' for x in maincmds]
    if LOG_COMMANDLINE:
        maincmds.append("sleep 10")
    with open(CMD_FILE_SAVE_DIR + 'main_init.txt', mode='w') as f:
        f.writelines(maincmds)

    if LOG_COMMANDLINE:
        maincmds.append("sleep 10")
    helpercmds = helpercmds[:]
    helpercmds[-1] += argstr
    helpercmds = [x + '\n' for x in helpercmds]
    helpercmds.append("sleep 5")
    with open(CMD_FILE_SAVE_DIR + 'helper_init.txt', mode='w') as f:
        f.writelines(helpercmds)

def gen_frames_imagehub():
    log_fun()
    global running, zoom, h, w, frame_width, frame_height, origin, image_hub, fill_height
    running = True
    image_hub = imagezmq.ImageHub()
    img = image_hub.recv_image()[1]
    image_hub.send_reply(b'OK')
    frame_height, frame_width = img.shape[:2]
    for i, r in img:
        if i < frame_height/2:
            if r[0] == np.array([0, 0, 0]):
                fill_height = i + 1
    while running:
        frame = image_hub.recv_image()[1][origin[1]:origin[1] + h, origin[0]:origin[0] + w]
        image_hub.send_reply(b'OK')
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', frame)[1].tobytes() + b'\r\n')
    image_hub.close()
    image_hub = -1

def gen_frames_imagehub_log_fps():
    log_fun()
    global running, zoom, h, w, frame_width, frame_height, origin, image_hub, fill_height
    running = True
    img_hub_fps, web_app_fps, t_old = [], [], 0
    image_hub = imagezmq.ImageHub()
    img = image_hub.recv_image()[1]
    image_hub.send_reply(b'OK')
    frame_height, frame_width = img.shape[:2]
    for i, r in img:
        if i < frame_height/2:
            if r[0] == np.array([0, 0, 0]):
                fill_height = i + 1
    while running:
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
    image_hub.close()
    image_hub = -1

def gen_placeholder_frame():
    img = cv2.imread(REPO_ROOT + "/web_ui/static/images/video_feed_placeholder.png")
    return b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', img)[1].tobytes() + b'\r\n'

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

# terminate()


@app.route('/', methods=['POST', 'GET'])
def index():
    global zoom, h, w, frame_width, frame_height, origin, blend_frac, resolution
    if request.method == 'POST':
        print(Fore.YELLOW + "POST", end=" " + Fore.RESET)
        cmd = request.form['button']
        print(cmd)
        if   cmd == 'poweron':
            initialize()
        elif cmd == 'poweroff':
            terminate()
        elif cmd == 'calibrate':
            terminate()
            gen_init_cmd_files(MAIN_INIT_CMDS, HELP_INIT_CMDS, 1, resolution, blend_frac, 0, PC_IP)
            initialize()
        elif cmd == 'setto180':
            terminate()
            # x_t = int(0.8 * resolution[0])
            x_t = 244
            gen_init_cmd_files(MAIN_INIT_CMDS, HELP_INIT_CMDS, 0, resolution, blend_frac, x_t, PC_IP)
            initialize()
        elif cmd == 'setto270':
            terminate()
            # x_t = int(0.08 * resolution[0])
            x_t = 28
            gen_init_cmd_files(MAIN_INIT_CMDS, HELP_INIT_CMDS, 0, resolution, blend_frac, x_t, PC_IP)
            initialize()
        elif cmd == 'decreaseblendfrac':
            if blend_frac > 0.1:
                blend_frac = round(blend_frac-0.1, 1)
            if blend_frac <= 0.1:
                blend_frac = 0
        elif cmd == 'increaseblendfrac':
            if blend_frac < 0.9:
                blend_frac = round(blend_frac+0.1, 1)
            if blend_frac >= 0.9:
                blend_frac = 1
        elif cmd == 'fullview':
            zoom = 0
            w = frame_width
            h = frame_height
            origin = [0, 0]
        elif cmd == 'fillview':
            zoom = 0
            origin = [0, 0]
            w = frame_width
            h = fill_height
        elif cmd == 'zoomin':
            if zoom < 0.4: # crash if allow higher zoom
                zoom += 0.05
                zoom = round(zoom, 2)
                w = int(frame_width*(1-2*zoom))
                h = int(frame_height*(1-2*zoom))
                origin = [int(frame_width*zoom), int(frame_height*zoom)]
        elif cmd == 'zoomout':
            if zoom > 0.05:
                zoom -= 0.05
                zoom = round(zoom, 2)
            elif zoom > 0:
                zoom = 0
            origin = [int(frame_width*zoom), int(frame_height*zoom)]
            w = int(frame_width*(1-2*zoom))
            h = int(frame_height*(1-2*zoom))
        elif cmd == 'panleft':
            if origin[0] > int(w*0.05):
                origin[0] -= int(w*0.05)
            elif origin[0] > 0:
                origin[0] = 0
        elif cmd == 'panright':
            if origin[0] + w + int(w*0.05) < frame_width:
                origin[0] += int(w*0.05)
            elif origin[0] + w < frame_width:
                origin[0] = frame_width - w
        elif cmd == 'panup':
            if origin[1] > int(h*0.05):
                origin[1] -= int(h*0.05)
            elif origin[1] > 0:
                origin[1] = 0
        elif cmd == 'pandown':
            if origin[1] + h + int(h*0.05) < frame_height:
                origin[1] += int(h*0.05)
            elif origin[1] + h < frame_height:
                origin[1] = frame_height - h
    else:
        print(Fore.YELLOW + "GET REQUEST" + Fore.RESET)
    return flask.render_template('index.html', blend_frac=blend_frac)


def refresh_video_feed(on=True):
    log_fun()
    if not(on):
        @app.route('/video_feed')
        def video_feed():
            return flask.Response(gen_placeholder_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')
    if LOG_FPS:
        @app.route('/video_feed')
        def video_feed():
            return flask.Response(gen_frames_imagehub_log_fps(), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        @app.route('/video_feed')
        def video_feed():
            return flask.Response(gen_frames_imagehub(), mimetype='multipart/x-mixed-replace; boundary=frame')

refresh_video_feed(False)
if __name__ == "__main__":
    app.run(debug=DEBUG)
