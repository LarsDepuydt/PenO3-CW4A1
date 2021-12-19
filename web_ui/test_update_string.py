
from re import X
import flask
from flask import request
import numpy as np
import cv2


flask.Response()
app = flask.Flask(__name__)

apples = 0

@app.route('/', methods=['POST', 'GET'])
def index():
    global apples
    if request.method == 'POST':
        if request.form['button'] == 'click':
            print("button clicked")
            apples += 1
    else:
        pass
    return flask.render_template('index3.html', apples=apples)

while True:
    apples += 1

    @app.route('/route1')
    def route1():
        def fun1():
            global apples
            yield str(apples)
        resp = app.response_class(fun1())
        resp.headers['X-Accel-Buffering'] = 'no'
        return resp

if __name__ == "__main__":
    app.run(debug=True)
