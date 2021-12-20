from re import X
import flask
from flask import request
import numpy as np
import cv2


flask.Response()
app = flask.Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def index():
    global x
    if request.method == 'POST':
        if request.form['button'] == 'click':
            print("button clicked")
            routesome(2)
    else:
        pass
    return flask.render_template('index5.html')


def fun1():
    return str(1)

def fun2():
    return str(2)

def routesome(n):
    if n == 1:
        @app.route('/route1')
        def route1():
            return flask.Response(fun1(), mimetype='text/plain')
    elif n == 2:
        @app.route('/route1')
        def route1():
            return flask.Response(fun2(), mimetype='text/plain')


if __name__ == "__main__":
    routesome(1)
    app.run(debug=True)
