import os
import time
import json
import logging

from flask import Flask, request, send_file, send_from_directory
from flask import jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, send

from io import BytesIO
from PIL import Image
from text_to_image import TextToImage

import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--world_instance',"-W", type=str, required=True, help='The path of the world instance (in world_instances/)')
args = parser.parse_args()



app = Flask(__name__, static_url_path='', static_folder='./frontend/dist') # create app with static folder
app.logger.setLevel(logging.INFO)
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=5, ping_interval=5) # create socket io
CORS(app)


# Project root directory
PARENT_DIR = os.path.abspath(os.path.dirname(__file__))

# Include assets including icons, tiles
ASSETS_DIR = os.path.join(PARENT_DIR, "assets")

# Environment path
ENV_PATH = os.path.join(f"{PARENT_DIR}/../world_instances/", f".{args.world_instance}.running")

if not os.path.exists(ENV_PATH):
    if os.path.exists(os.path.join(f"{PARENT_DIR}/../world_instances/", args.world_instance)):
        raise RuntimeError(f"Found static files of world: {args.world_instance}, but it has been copied into the running folder. Please start the engine by running `python gptworld/run.py -W {args.world_instance}` first.")
    else:
        raise RuntimeError(f"No world instance named {args.world_instance} has been found.")


#-------------------------------- Implement Text to Image -------------------------------
text_to_icon = TextToImage(ASSETS_DIR, "icon")
text_to_tile = TextToImage(ASSETS_DIR, "tile")

@app.route('/text_to_icon', methods=['GET'])
def text_to_icon_route():
    name = request.args.get('name')
    if name == []:
        return "Failed to find image for your requested text."
    image = text_to_icon.query(name)[0]
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/text_to_tile', methods=['GET'])
def text_to_tile_route():
    name = request.args.get('name')
    if name == []:
        return "Failed to find image for your requested text."
    image = text_to_tile.query(name)[0]
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

def add_object_embedding():
    embedding_path = os.path.join(ENV_PATH, 'embeddings.json')
    with open(embedding_path, 'r') as f:
        content = json.load(f)
    
    # Update the TextToImage module
    for name in content.keys():
        embedding = content[name]
        text_to_icon.add_existing_object(name, embedding)
        text_to_tile.add_existing_object(name, embedding)

add_object_embedding()
# -----------------------------------------------------------------------------------------


# ----------------------------- Implement Realtime UI Logging ------------------------------------
clients = []

@socketio.on('connect')
def on_connect():
    global clients
    sid = request.sid
    clients.append(sid)
    print('Client connected, sid:', sid)
    emit('welcome', {'message': 'Welcome, this is a test message!'})
    socketio.start_background_task(uilogging, sid)

@socketio.on('disconnect')
def on_disconnect():
    global clients
    sid = request.sid
    clients.remove(sid)
    print(f'====================== Client disconnected, sid:{sid} ==========================')

def read_new_lines(file_path, last_position):
    new_lines = []
    if not os.path.exists(file_path):
        return [], None
    with open(file_path, 'r', encoding='utf-8') as file:
        if last_position is None:
            file.seek(0, os.SEEK_END)  # move file pointer to last position
            last_position = file.tell()
        else:
            file.seek(last_position)  # move file pointer to last read position
        
        new_data = file.read()
        last_position = file.tell()  # update file pointer

        if new_data:
            new_lines = new_data.splitlines()

    return new_lines, last_position

def uilogging(sid: str):
    """ This function will act as a thread to send latest UI logs to client of given session id 'sid'
    """
    file_path = os.path.join(ENV_PATH, 'uilogging.txt')
    last_position = None

    while sid in clients: # if the client is closed, this thread will terminate
        # print('read_new_lines invoked!')
        new_lines = []

        new_lines, last_position = read_new_lines(file_path, last_position)
        for line in new_lines:
            print(line)
            pass
        if new_lines != []: # only if there is new messages will socketio send messages to client
            socketio.emit('server_message', {"message": new_lines})
        
        time.sleep(1)
    
    return
# ----------------------------------------------------------------------------------------


# ----------------------------- Static Files (Frontend dist) --------------------------------
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_file(path):
    return send_from_directory(app.static_folder, path)
# -------------------------------------------------------------------------------------------


@app.route('/read_environment', methods=['GET'])
def read_environment():
    environment_main_path = os.path.join(ENV_PATH, 'environment.json')
    with open(environment_main_path, 'r') as f:
        content = json.load(f)
    data = {'message': content}
    return jsonify(data)

def drop_invoice(invoice: str):
    """
    drop invoice to a file for the agent to be notified.
    TODO: later connect with the HTML <text>
    """
    INVOICE_PATH = os.path.join(ENV_PATH, "invoice.txt")
    with open(INVOICE_PATH, 'w') as fp:
        print(str, fp)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
    # app.run(host='0.0.0.0', port=5001, debug=True)
    