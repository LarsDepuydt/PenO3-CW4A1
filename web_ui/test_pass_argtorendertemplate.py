import flask
from flask import request

A = 0.5

flask.Response()
app = flask.Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def index():
    global A
    if request.method == 'POST':
        if request.form['button'] == 'decreaseblendfrac':
            print("Decreasing blend frac...")
            if A > 0.1:
                A = round(A-0.1, 1)
            if A <= 0.1:
                A = 0
        elif request.form['button'] == 'increaseblendfrac':
            print("Increasing blend frac...")
            if A < 0.9:
                A = round(A+0.1, 1)
            if A >= 0.9:
                A = 1
        else:
            print("UNKNOWN POST REQUEST")
    else:
        print("NON-POST REQUEST")
        pass
    return flask.render_template('index.html', blend_frac = A)

@app.route('/video_feed',methods=['POST', 'GET'])
def video_feed():
    return "Yobama"

if __name__ == "__main__":
    app.run(debug=True)
