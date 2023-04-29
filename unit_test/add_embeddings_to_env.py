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


    with open(file_path+".embeddings.json", "w") as f:
        json.dump(embedding_map, f)

if __name__ == "__main__":
    gen_env_logo_embeddings("static_files/debating_room/environment.json")
