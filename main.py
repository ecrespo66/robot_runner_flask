import json
import flask
from flask import jsonify, request
from server import Server
app = flask.Flask(__name__)
app.config["DEBUG"] = False


@app.route('/status', methods=['GET'])
def get_robot_status():
    print(server.status)
    return jsonify(server.status)


@app.route('/block', methods=['GET'])
def set_robot_status():
    server.status = "blocked"
    response = app.response_class(
        response=json.dumps({'message': "blocked"}),
        status=300,
        mimetype='application/json')
    return response


@app.route('/run', methods=['POST'])
def run_robot():
    data = request.json
    try:
        print(data)
        server.run(data)
        message = json.dumps({'message': "running"})
        status = 200
        response = app.response_class(
            response=message,
            status=status,
            mimetype='application/json')
        server.status = "free"
    except Exception as e:
        print(e)
        server.status = "free"
        response = app.response_class(
            response=json.dumps({'message': e.__str__()}),
            status=400,
            mimetype='application/json')
    return response


@app.route('/stop', methods=['GET'])
def stop_robot():
    try:
        server.stop()
        response = app.response_class(
            response=json.dumps({'message': "OK"}),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        response = app.response_class(
            response=json.dumps({'message': e.__str__()}),
            status=200,
            mimetype='application/json'
        )
    return response


@app.route('/pause', methods=['GET'])
def pause_robot():
    try:
        server.pause()
        response = app.response_class(
            response=json.dumps({'message': "OK"}),
            status=200,
            mimetype='application/json')
    except Exception as e:
        response = app.response_class(
            response=json.dumps({'message': e.__str__()}),
            status=200,
            mimetype='application/json')
    return response


@app.route('/resume', methods=['GET'])
def resume_robot():
    try:
        server.resume()
        response = app.response_class(
            response=json.dumps({'message': "OK"}),
            status=200,
            mimetype='application/json')
    except Exception as e:
        print(e)
        response = app.response_class(
            response=json.dumps({'message': e.__str__()}),
            status=200,
            mimetype='application/json')
    return response


if __name__ == '__main__':

    server = Server()
    app.run(host='0.0.0.0', port=8088, debug=True)

    # from waitress import serve
    # serve(app, host="0.0.0.0", port=80)
