from flask import Flask, request, send_file
import os
from flask import jsonify
from flask_cors import CORS
import json
from PIL import Image
from io import BytesIO
from backend.text_to_image import TextToImage


PARENT_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)

################ Implement Text to Image ###############

ASSETS_DIR = os.path.join(PARENT_DIR, "assets")
text_to_icon = TextToImage(ASSETS_DIR, "icon")
text_to_tile = TextToImage(ASSETS_DIR, "tile")

@app.route('/text_to_icon', methods=['GET'])
def text_to_icon_route():
    name = request.args.get('name')
    image = text_to_icon.query(name)[0]
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/text_to_tile', methods=['GET'])
def text_to_tile_route():
    name = request.args.get('name')
    image = text_to_tile.query(name)[0]
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

########################################################


@app.route('/read_environment', methods=['GET'])
def read_environment():

    file_path = request.args.get('file_path')
    with open(f"{PARENT_DIR}/../../static_files/{file_path}", 'r') as f:
        content = json.load(f)
    
    # Update the TextToImage module
    for item in content["areas"].values():
        text_to_tile.add_existing_object(item["name"], item["embedding"])
        item["embedding"] = None
    
    for item in content["objects"].values():
        text_to_icon.add_existing_object(item["name"], item["embedding"])
        item["embedding"] = None

    data = {'message': content}
    return jsonify(data)


# @socketio.on('tunnel')
# def handle_message(message):
#     print('Received message: ' + message)
#     emit('response', {'data': message})


if __name__ == '__main__':
    app.run(port=5001, debug=True)