import json
# Import OpenAI language model
from gptworld.models.openai_api import get_embedding

with open("./outputs/environment.json", "r") as f:
    data = json.load(f)

areas = data["areas"]
objects = data["objects"]


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
    embedding_map[name] = embedding

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
    embedding_map[name] = embedding

with open("./outputs/embeddings.json", "w") as f:
    json.dump(embedding_map, f)




