import json
import requests
from typing import List
from gptworld.models.openai_api import get_embedding


def gen_env_logo_embeddings(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)

    areas = data.get("areas", {})
    objects = data.get("objects", {})


    embedding_map = {}


    for i in areas.keys():
        item = areas[i]
        name = item["name"]
        max_retry = 10
        retry = 0
        embedding = []
        while retry <= max_retry:
            try:
                retry += 1
                embedding = get_embedding(name)
                print("ok")
                break
            except:
                print("exception")
                continue
        # item["embedding"] = embedding
        embedding_map[name] = embedding
        # areas[i] = item
        # break

    for i in objects.keys():
        item = objects[i]
        name = item["name"]
        max_retry = 10
        retry = 0
        embedding = []
        while retry <= max_retry:
            try:
                retry += 1
                embedding = get_embedding(name)
                print("ok")
                break
            except:
                print("exception")
                continue
        # item["embedding"] = embedding
        embedding_map[name] = embedding
        # break

    file_dir = os.path.dirname(file_path)
    with open(os.path.join(file_dir,"embeddings.json"), "w") as f:
        json.dump(embedding_map, f)

if __name__ == "__main__":
    # Project root directory
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument('--world_instance',"-W", type=str, required=True, help='The path of the world instance (in world_instances/)')
    args = parser.parse_args()
    PARENT_DIR = os.path.abspath(os.path.dirname(__file__))
    gen_env_logo_embeddings(os.path.join(PARENT_DIR, f"../world_instances/{args.world_instance}/environment.json"))
