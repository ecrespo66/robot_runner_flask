import flask
from flask import jsonify, request
from server import Server

app = flask.Flask(__name__)
app.config["DEBUG"] = False


@app.route('/status', methods=['GET'])
def get_robot_status():
    return jsonify(server.get_status())


@app.route('/run', methods=['POST'])
def run_robot():
    data = request.json
    server.run(data)
    return request


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
    server.set_status("running")
    app.run(host=server.ip, port=server.port, debug=True)
