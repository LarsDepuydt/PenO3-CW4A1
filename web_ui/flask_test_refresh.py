from re import X
import flask
from flask import request
import numpy as np
import cv2


flask.Response()
app = flask.Flask(__name__)

x = 0

@app.route('/', methods=['POST', 'GET'])
def index():
    global x
    if request.method == 'POST':
        if request.form['button'] == 'click':
            print("button clicked")
            import time
            time.sleep(10)
            print("continuing")
    else:
        pass
    return flask.render_template('index2.html')


def fun1():
    import time
    global x
    i1 = 0
    while True:
        i1 += 1
        x += 1
        print("1:", i1, x)
        time.sleep(1)

def fun2():
    import time
    global x
    i2 = 0
    while True:
        i2 += 1
        x += 1
        print("---2:", i2, x)
        time.sleep(1)


@app.route('/route1')
def route1():
    return flask.Response(fun1(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/route2')
def route2():
    return flask.Response(fun2(), mimetype='multipart/x-mixed-replace; boundary=frame')

'''
When you refresh, the previous route function does not stop running
When you time.sleep in route, other routes dont sleep
'''


if __name__ == "__main__":
    app.run(debug=True)
