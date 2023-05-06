import os
import time
import json
from functools import lru_cache
import logging
import numpy as np
from scipy.spatial import distance
from typing import List, Dict

from flask import Flask, request, send_file, send_from_directory
from flask import jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, send

from io import BytesIO
from PIL import Image

import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--world_instance',"-W", type=str, required=True, help='The path of the world instance (in world_instances/)')
args = parser.parse_args()

# Project root directory
PARENT_DIR = os.path.abspath(os.path.dirname(__file__))

# Pre-compiled frontend path
FRONTEND_PATH = os.path.join(PARENT_DIR, "frontend_new/rpg-game/build")

# Include assets including icons, tiles
ASSETS_DIR = os.path.join(PARENT_DIR, "assets")

# World instance path
ENV_PATH = os.path.join(f"{PARENT_DIR}/../world_instances/", f".{args.world_instance}.running")

# Check if world instance exist
if not os.path.exists(ENV_PATH):
    if os.path.exists(os.path.join(f"{PARENT_DIR}/../world_instances/", args.world_instance)):
        # raise RuntimeError(f"Found static files of world: {args.world_instance}, but it has been copied into the running folder. Please start the engine by running `python gptworld/run.py -W {args.world_instance}` first.")
        print("Warning: You are under static viewing mode, the world instance is frozen.")
        ENV_PATH = os.path.join(f"{PARENT_DIR}/../world_instances/", f"{args.world_instance}")
    else:
        raise RuntimeError(f"No world instance named {args.world_instance} has been found.")

# Global variables
environment_config_file = None
predefined_text_to_image_mapping = {}

# Create flask app with static folder
app = Flask(__name__, static_url_path='', static_folder=FRONTEND_PATH) 
app.logger.setLevel(logging.INFO)

# create socket io
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=5, ping_interval=5) 

CORS(app)


# Static Files (pre-compiled frontend)
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_file(path):
    return send_from_directory(app.static_folder, path)


# read_environment API
@app.route('/read_environment', methods=['GET'])
def read_environment():
    global environment_config_file
    global predefined_text_to_image_mapping
    
    environment_main_path = os.path.join(ENV_PATH, 'environment.json')
    with open(environment_main_path, 'r') as f:
        content = json.load(f)
        environment_config_file = content
    
    # Build predefined text to image mapping (if exist)
    predefined_text_to_image_mapping = {}
    for key in environment_config_file["objects"]:
        value = environment_config_file["objects"][key]
        predefined_text_to_image_mapping[value["name"]] = value.get("predefined_texture", None)
    for key in environment_config_file["areas"]:
        value = environment_config_file["areas"][key]
        predefined_text_to_image_mapping[value["name"]] = value.get("predefined_texture", None)
    
    data = {'message': content}
    return jsonify(data)


# Implement Semantic Matching 
class SemanticMatching:
    def __init__(self, assets_dir: str, world_instance_path: str, category: str):
        self.assets_dir = assets_dir
        self.world_instance_path = world_instance_path
        self.category = category
        self.existing_object_name_to_embedding = {}
        
        # Build a map of image path -> semantic embedding vectors
        self.image_path_to_embedding = {}

        # Load semantic embeddings from image library
        try:
            image_library_embedding_path = os.path.join(self.assets_dir, f'{self.category}_embeddings.jsonl')
            with open(image_library_embedding_path, 'r', encoding='utf-8') as f:
                image_data = [json.loads(line) for line in f]
            for item in image_data:
                path = item["path"]
                embedding = item["embedding"]
                self.image_path_to_embedding[path] = embedding
            print(f"Loaded {self.category} embeddings")
        except:
            print(f"Failed to load {self.category} embeddings")
        
        # Load semantic embeddings from image library from environment
        try:
            embedding_path = os.path.join(self.world_instance_path, 'embeddings.json')
            with open(embedding_path, 'r') as f:
                content = json.load(f)
            
            # Update the TextToImage module
            for name in content.keys():
                embedding = content[name]
                self.existing_object_name_to_embedding[name] = embedding
        except:
            print("An error occured while add named entity embeddings, continue...")

        return

    @classmethod
    def find_most_similar_list(cls, query: List[float], database: Dict[str, List[float]]) -> List[str]:
        """ find the most similar icons for new query in predefined database
        """
        cosine_similarities = {k: np.dot(query, v) / (np.linalg.norm(query) * np.linalg.norm(v)) for k, v in database.items()}
        most_similar_key = max(cosine_similarities, key=cosine_similarities.get)
        return most_similar_key
    
    @lru_cache(maxsize=512)
    def query(self, name: str):
        """ Find top icons according to a query, use cache to avoid redundant computation
        """
        # First get the embedding of query word
        query_vector = self.existing_object_name_to_embedding.get(name, None)
        if query_vector is None:
            # print("error")
            return None
        
        # After getting the query embedding, find the top icon names
        top_icon_path = self.find_most_similar_list(query_vector, self.image_path_to_embedding)

        # Return full path of images
        full_path = os.path.join(self.assets_dir, self.category, top_icon_path)

        print("Full paths", full_path)

        return full_path


# Initialize TextToImage functional object
text_to_icon = SemanticMatching(ASSETS_DIR, ENV_PATH, "icon")
text_to_tile = SemanticMatching(ASSETS_DIR, ENV_PATH, "tile")


# text_to_icon API
@app.route('/text_to_icon', methods=['GET'])
def text_to_icon_route():
    global environment_config_file
    global predefined_text_to_image_mapping
    
    name = request.args.get('name')
    
    if environment_config_file is None:
        read_environment()
    
    predefined_relative_path = predefined_text_to_image_mapping.get(name, None)
    
    if predefined_relative_path is not None:
        # Case 1: If the texture is predefined, use predefined texture
        full_path = os.path.join(ENV_PATH, predefined_relative_path)
    else:
        # Case 2: If no predefined texture, use semantic matching
        full_path = text_to_icon.query(name)
    
    # Load image from file system and return to clients
    image = Image.open(full_path)
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

# text_to_tile API
@app.route('/text_to_tile', methods=['GET'])
def text_to_tile_route():
    global environment_config_file
    global predefined_text_to_image_mapping
    
    if environment_config_file is None:
        read_environment()
    
    name = request.args.get('name')
    
    predefined_relative_path = predefined_text_to_image_mapping.get(name, None)
    
    print("Texture: ", ENV_PATH, predefined_relative_path)
    if predefined_relative_path is not None:
        # Case 1: If the texture is predefined, use predefined texture
        
        full_path = os.path.join(ENV_PATH, predefined_relative_path)
    else:
        # Case 2: If no predefined texture, use semantic matching
        full_path = text_to_tile.query(name)

    # Load image from file system and return to clients
    image = Image.open(full_path)
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


# Implement Realtime UI Logging
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

# Drop invoice API
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
    