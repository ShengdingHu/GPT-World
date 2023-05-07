import json
import requests
import os
from typing import List
from gptworld.models.openai_api import get_embedding


def make_entity_embedding(env_path):
    with open(os.path.join(env_path, 'environment.json'), "r") as f:
        data = json.load(f)

    areas = data.get("areas", {})
    objects = data.get("objects", {})

    embedding_map = {}

    counter = 0
    total = len(areas)
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
                counter += 1
                print(f"ok {counter}/{total}")
                break
            except:
                print("exception")
                continue
        embedding_map[name] = embedding

    counter = 0
    total = len(objects)
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
                counter += 1
                print(f"ok {counter}/{total}")
                break
            except:
                print("exception")
                continue
        embedding_map[name] = embedding

    with open(os.path.join(env_path, "embeddings.json"), "w") as f:
        json.dump(embedding_map, f)

if __name__ == "__main__":
    # Project root directory
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument('--world_instance',"-W", type=str, required=True, help='The path of the world instance (in world_instances/)')
    args = parser.parse_args()
    PARENT_DIR = os.path.abspath(os.path.dirname(__file__))
    make_entity_embedding(os.path.join(PARENT_DIR, "../../world_instances/alice_home"))

