import cv2
import time
import imagezmq
import flask
import numpy as np
from colorama import Fore, Back, Style

# REFERENCE: https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/
# REFERENCE: https://towardsdatascience.com/video-streaming-in-web-browsers-with-opencv-flask-93a38846fe00

# ==============================
# CONSTANTS
# ==============================

X_T_FRAC = {180: 0.7625, 360: 0.0875}

LOG_FPS          = False
DEBUG            = False
SLEEP_PI_CMDLINE = True

running     = False
image_hub   = -1
resolution  = [320, 240]
blend_frac  = 0.5
x_t         = 0
calibrate   = False
frame_width, frame_height = 1000, 240    # placeholder for frame_width and frame_height
fill_height = int(0.9*frame_height)
w, h        = frame_width, frame_height  # shown frame width (for zooming)
zoom        = 0
origin      = [0, 0]

from os import path
REPO_ROOT               =  str(path.dirname(path.realpath(__file__)))[:-7].replace("\\", "/")
PROG_DIR                = REPO_ROOT+ "/programs/non_multi_threaded"
REMOTE_EXEC_SCRIPT_PATH = PROG_DIR + "/ssh_conn_exec_cmdfile_win.bat"
MAIN_INIT_CMD_FILE_PATH = PROG_DIR + "/main_init.txt"
HELP_INIT_CMD_FILE_PATH = PROG_DIR + "/help_init.txt"
MAIN_TERM_CMD_FILE_PATH = PROG_DIR + "/main_term.txt"
HELP_TERM_CMD_FILE_PATH = PROG_DIR + "/help_term.txt"

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
    'echo "IN MAIN PI: terminating all python"',
    'sudo pkill python']

HELP_TERM_CMDS = [
    'echo "IN HELPER PI: terminating all python"',
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
HELP_PI_IP = "169.254.222.67"


# ==============================
# FUNCTIONS
# ==============================

def log_fun():
    import inspect
    print(Fore.CYAN + "FUNCTION " + Fore.RESET + str(inspect.stack()[1][3]) + "()")

def check_availability_pis():
    from subprocess import check_output
    out_main = str(check_output("ping -n 2 " + MAIN_PI_IP))
    out_help = str(check_output("ping -n 2 " + HELP_PI_IP))
    error = False
    if out_main.find("host unreachable") != -1:
        print(Fore.RED + "ERROR " + Fore.RESET + "Main pi unreachable")
        error = True
    else:
        print(Fore.GREEN + "SUCCES " + Fore.RESET + "Main pi is reachable")
    if out_help.find("host unreachable") != -1:
        print(Fore.RED + "ERROR " + Fore.RESET + "Help pi unreachable")
        error = True
    else:
        print(Fore.GREEN + "SUCCES " + Fore.RESET + "Help pi is reachable")
    return not(error)

def initialize_pis():
    log_fun()
    global running
    running = True
    from subprocess import run, DEVNULL
    run([REMOTE_EXEC_SCRIPT_PATH, 'MAIN PI - INITIALIZING', MAIN_PI_IP, MAIN_INIT_CMD_FILE_PATH], stdout=DEVNULL)
    run([REMOTE_EXEC_SCRIPT_PATH, 'HELP PI - INITIALIZING', HELP_PI_IP, HELP_INIT_CMD_FILE_PATH], stdout=DEVNULL)

def terminate_pis():
    log_fun()
    from time import sleep
    global running
    # wait until gen_frames_imagehub() has gone out of loop and closed imagehub: 
    running = False
    while True:             
        if image_hub == -1:
            break
        else:
            sleep(0.5)
    from subprocess import run, DEVNULL
    run([REMOTE_EXEC_SCRIPT_PATH, "MAIN PI - TERMINATING", MAIN_PI_IP, MAIN_TERM_CMD_FILE_PATH], stdout=DEVNULL)
    run([REMOTE_EXEC_SCRIPT_PATH, "HELP PI - TERMINATING", HELP_PI_IP, HELP_TERM_CMD_FILE_PATH], stdout=DEVNULL)

def gen_init_cmd_files(use_keypnt, res, blend_frac, x_t, pc_ip):
    log_fun()
    sp = '" "'
    argstr = ' "' +  str(use_keypnt) + sp + str(res[0])+","+str(res[1]) + sp + str(blend_frac) + sp + str(x_t) + sp + pc_ip + '"'
    
    def write_file(cmds, filepath):
        cmds = cmds[:]
        cmds[-1] += argstr
        cmds = [x + '\n' for x in cmds]
        if SLEEP_PI_CMDLINE:
            cmds.append("sleep 10")
        with open(filepath, mode='w') as f:
            f.writelines(cmds)
            
    write_file(MAIN_INIT_CMDS, MAIN_INIT_CMD_FILE_PATH)
    write_file(HELP_INIT_CMDS, HELP_INIT_CMD_FILE_PATH)

def gen_term_cmd_files():
    log_fun()
    def write_file(cmds, filepath):
        cmds = cmds[:]
        cmds = [x + '\n' for x in cmds]
        if SLEEP_PI_CMDLINE:
            cmds.append("sleep 10")
        with open(filepath, mode='w') as f:
            f.writelines(cmds)
    
    write_file(MAIN_TERM_CMDS, MAIN_TERM_CMD_FILE_PATH)
    write_file(HELP_TERM_CMDS, HELP_TERM_CMD_FILE_PATH)

def gen_frames():
    log_fun()
    from time import sleep
    global running, zoom, h, w, frame_width, frame_height, origin, image_hub, fill_height
    while True:
        if not(running):
            print(Fore.MAGENTA + "RUNNING " + Fore.RESET + "PlaceHolder")
            img = cv2.imread(REPO_ROOT + PLACEHOLDER_PATH)
            while not(running):
                yield b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', img)[1].tobytes() + b'\r\n'
                sleep(0.5)
        else:
            print(Fore.MAGENTA + "RUNNING " + Fore.RESET + "ImageHub")
            image_hub = imagezmq.ImageHub()
            print("waiting for image")
            img = image_hub.recv_image()[1]
            print("Received image")
            image_hub.send_reply(b'OK')
            frame_height, frame_width = img.shape[:2]
            for i, r in enumerate(img):
                if i < frame_height/2:
                    print(r[0])
                    if (int(r[0][0]), int(r[0][1]), int(r[0][2]))  == [0, 0, 0]:
                        fill_height = i + 1
            while running:
                frame = image_hub.recv_image()[1][origin[1]:origin[1] + h, origin[0]:origin[0] + w]
                image_hub.send_reply(b'OK')
                yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', frame)[1].tobytes() + b'\r\n')
            image_hub.close()
            image_hub = -1

def gen_frames_log_fps():
    log_fun()
    from time import sleep
    global running, zoom, h, w, frame_width, frame_height, origin, image_hub, fill_height
    while True:
        if not(running):
            print(Fore.MAGENTA + "RUNNING " + Fore.RESET + "PlaceHolder")
            img = cv2.imread(REPO_ROOT + PLACEHOLDER_PATH)
            while not(running):
                yield b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', img)[1].tobytes() + b'\r\n'
                sleep(0.5)
        else:
            print(Fore.MAGENTA + "RUNNING " + Fore.RESET + "ImageHub")
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
                
                t_after_yield = time.perf_counter()
                web_app_fps.append(1/(t_after_yield - t_after_image))
                img_hub_fps.append(1/(t_after_image - t_old))
                t_old = t_after_image

                if len(web_app_fps) == 50:
                    print("Webapp fps 50avg     : ", sum(web_app_fps)/50)
                    print("Webapp fps 1sample   : ", web_app_fps[-1])
                    print("Imagehub fps 50avg   : ", sum(img_hub_fps)/50)
                    print("Imagehub fps 1sample : ", img_hub_fps[-1])
                    web_app_fps, img_hub_fps = [], []
            image_hub.close()
            image_hub = -1


# ==============================
# FLASK
# ==============================

flask.Response()
app = flask.Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def index():
    global zoom, h, w, frame_width, frame_height, origin, blend_frac, resolution
    if flask.request.method == 'POST':
        cmd = flask.request.form['button']
        print(Fore.YELLOW + "POST", end=" " + Fore.RESET)
        print(cmd)
        if   cmd == 'poweron':
            initialize_pis()
        elif cmd == 'poweroff':
            terminate_pis()
        elif cmd == 'calibrate':
            terminate_pis()
            gen_init_cmd_files(1, resolution, blend_frac, 0, PC_IP)
            initialize_pis()
        elif cmd == 'setto180':
            terminate_pis()
            # x_t = int(0.8 * resolution[0])
            x_t = 244
            gen_init_cmd_files(0, resolution, blend_frac, x_t, PC_IP)
            initialize_pis()
        elif cmd == 'setto270':
            terminate_pis()
            # x_t = int(0.08 * resolution[0])
            x_t = 28
            gen_init_cmd_files(0, resolution, blend_frac, x_t, PC_IP)
            initialize_pis()
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
        print(Fore.YELLOW + "GET" + Fore.RESET)
    return flask.render_template('index4.html', blend_frac=blend_frac)

if LOG_FPS:
    @app.route('/video_feed')
    def video_feed():
        return flask.Response(gen_frames_log_fps(), mimetype='multipart/x-mixed-replace; boundary=frame')
else:
    @app.route('/video_feed')
    def video_feed():
        return flask.Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    gen_term_cmd_files()
    if check_availability_pis():
        terminate_pis()
        PLACEHOLDER_PATH = "/web_ui/static/images/video_feed_placeholder.png"
    else:
        PLACEHOLDER_PATH = "/web_ui/static/images/video_feed_placeholder_pis_unavailable.png"
    app.run(debug=DEBUG)
