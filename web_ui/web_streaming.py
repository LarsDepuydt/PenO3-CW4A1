import flask, cv2, time

# REFERENCE: https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/
# REFERENCE: https://towardsdatascience.com/video-streaming-in-web-browsers-with-opencv-flask-93a38846fe00

app = flask.Flask(__name__)

#vs = VideoStream(usePiCamera=1).start() # pi camera
#time.sleep(2.0)

camera = cv2.VideoCapture(0)    # laptop webcam

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

def gen_frames():
    while True:
        succes, frame = camera.read()
        if not succes:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return flask.Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True)
