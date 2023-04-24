import json
import requests
from typing import List
import os

def chat(context, MAX_OUTPUT_TOKEN_LEN=1024,temperature=0.5) -> str:
    if isinstance(context, str):
        context = [{"role": "user", "content": context}]
    url = "http://freegpt.club/gptworld_chat"
    headers={"Content-Type":"application/json"}
    session = requests.Session()
    data = {
        "model": "gpt-3.5-turbo",
        "messages": context,
        "max_tokens": MAX_OUTPUT_TOKEN_LEN,
        "temperature": temperature,
    }

    jsondata = json.dumps(data)
    res = session.post(url = url, data = jsondata, headers = headers)
    print("->", res.text)
    response_dict = json.loads(res.text.strip())
    # print(response_dict)
    try:
        return response_dict['choices'][0]['message']['content'].strip()
    except:
        return ""


def get_embedding(text: str) -> List[float]:
    # if os.environ['OPENAI_METHOD'] == 'pool':  # TODO, remove this in public version.
    if True:
        url = "http://freegpt.club/gptworld_embedding"
        headers={"Content-Type":"application/json"}
        session = requests.Session()
        data = {
            "model": "text-embedding-ada-002",
            "input": text
        }

        jsondata = json.dumps(data)
        res = session.post(url = url, data = jsondata, headers = headers)

        print("->", res.text)

        # print(res)
        response_dict = json.loads(res.text.strip())
        try:
            return response_dict['data'][0]['embedding']
        except:
            return []
    elif os.environ['OPENAI_METHOD'] == "api_key":
        text = text.replace("\n", " ")
        embedding = openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]
        return embedding



if __name__ == "__main__":
    print(get_embedding("hello world"))
    print(chat([{"role": "user", "content": "hello!"}]))