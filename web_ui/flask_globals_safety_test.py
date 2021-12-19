from re import X
import flask
from flask import request
import numpy as np
import cv2

# ==============================
# FLASK
# ==============================

w, h = 2000, 2000

flask.Response()
app = flask.Flask(__name__)

x = np.zeros((h,w,3), np.uint8)

@app.route('/', methods=['POST', 'GET'])
def index():
    global x
    if request.method == 'POST':
        if request.form['button'] == 'click':
            print("button clicked")
            
    else:
        pass
    return flask.render_template('index2.html', apple=x)


def fun1():
    import time
    global x, h, w
    black = True
    while True:
        if black:
            x = 255*np.ones((h,w,3), np.uint8)
            black=False
        else:
            x = np.zeros((h,w,3), np.uint8)
            black = True
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', x)[1].tobytes() + b'\r\n')
        time.sleep(1)

def fun2():
    import time
    global x, h, w
    red = True
    i = 0
    while True:
        if i <= 10:
            if red:
                x = np.zeros((h,w,3), np.uint8)
                x[:,:,0] = 255
                red = False
            else:
                x = np.zeros((h,w,3), np.uint8)
                x[:,:,2] = 255
                red = True
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', x)[1].tobytes() + b'\r\n')
        time.sleep(1)
        i += 1

@app.route('/route1')
def route1():
    return flask.Response(fun1(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/route2')
def route2():
    return flask.Response(fun2(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(debug=True)
