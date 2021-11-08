import flask, cv2, time, imagezmq

# REFERENCE: https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/
# REFERENCE: https://towardsdatascience.com/video-streaming-in-web-browsers-with-opencv-flask-93a38846fe00

MODE = 1

if MODE == 1:
    camera = cv2.VideoCapture(0)    # laptop webcam
elif MODE == 2: 
    import imutils
    vs = imutils.VideoStream(usePiCamera=True).start() # pi camera
    time.sleep(2.0)
elif MODE == 3:
    IMAGE_HUB = imagezmq.ImageHub()


app = flask.Flask(__name__)


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

def gen_frames_webcam():
    frames_per_second, t_old = [], 0
    while True:
        t = time.perf_counter()
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

def gen_frames_imagehub():
    image_hub_fps, webserver_fps, t_old = [], [], 0
    while True:
        t = time.perf_counter()

        frame = IMAGE_HUB.recv_image()[1]
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        webserver_fps.append(1/(t-t_old))
        t = time.perf_counter()
        image_hub_fps.append(1/(t-t_old))
        t_old = t

        if len(webserver_fps) == 10:
            print("Webserver fps 10avg: ", sum(webserver_fps)/10)
            print("Imagehub fps 10avg: ", sum(image_hub_fps)/10)
            print("Webserver fps instant: ", webserver_fps[-1])
            print("Webserver fps instant: ", image_hub_fps[-1])
            webserver_fps, image_hub_fps = [], []


def gen_frame_counter():
    i = 0
    while True:
        j = str(i).to_bytes
        yield(b'Content-Type: text' + j)
        i += 1
        time.sleep(0.2)
        print(i)


@app.route('/')
def index():
    return flask.render_template('index.html')

if MODE == 1 or MODE == 2:
    @app.route('/video_feed')
    def video_feed():
        return flask.Response(gen_frames_webcam(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
elif MODE == 3:
    @app.route('/video_feed')
    def video_feed():
        return flask.Response(gen_frames_imagehub(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True)
