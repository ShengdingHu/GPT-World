from flask import Flask, request
import os
from flask import jsonify
from flask_cors import CORS
import json

PARENT_DIR = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
CORS(app)

@app.route('/read_file', methods=['GET'])
def read_file_route():
    file_path = request.args.get('file_path')
    with open(f"{PARENT_DIR}/../../static_files/{file_path}", 'r') as f:
        content = json.load(f)
    
    data = {'message': content}
    return jsonify(data)


if __name__ == '__main__':
    app.run(port=5001, debug=True)