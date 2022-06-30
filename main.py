import json

import flask
from flask import jsonify, request
from server import Server
import threading
app = flask.Flask(__name__)
app.config["DEBUG"] = False


@app.route('/status', methods=['GET'])
def get_robot_status():
    return jsonify(server.get_status())


@app.route('/run', methods=['POST'])
def run_robot():
    data = request.json
    #t1 = threading.Thread(target=server.run, args=(data,), daemon=True)
    #t1.start()

    response = app.response_class(
        response=json.dumps({"Data": "Sucessful"}),
        status=200,
        mimetype='application/json'
    )
    return response, server.run(data)


@app.route('/stop', methods=['GET'])
def stop_robot():
    server.stop()
    return request


@app.route('/pause', methods=['GET'])
def pause_robot():
    server.pause()
    return request


@app.route('/resume', methods=['GET'])
def resume_robot():
    server.resume()
    return request


if __name__ == '__main__':
    server = Server()
    app.run(host=server.ip, port=server.port, debug=True)
