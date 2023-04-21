import json
import requests
from typing import List


def chat(context, MAX_OUTPUT_TOKEN_LEN=1024) -> str:
    if isinstance(context, str):
        context = [{"role": "user", "content": context}]
    url = "http://freegpt.club/gptworld_chat"
    headers={"Content-Type":"application/json"}
    session = requests.Session()
    data = {
        "model": "gpt-3.5-turbo",
        "messages": context,
        "max_tokens": MAX_OUTPUT_TOKEN_LEN,
        "temperature": 0.5,
    }

    jsondata = json.dumps(data)
    res = session.post(url = url, data = jsondata, headers = headers)
    response_dict = json.loads(res.text.strip())
    # print(response_dict)
    try:
        return response_dict['choices'][0]['message']['content'].strip()
    except:
        return ""


def embedding(text: str) -> List[float]:
    url = "http://freegpt.club/gptworld_embedding"
    headers={"Content-Type":"application/json"}
    session = requests.Session()
    data = {
        "model": "text-embedding-ada-002",
        "input": text
    }

    jsondata = json.dumps(data)
    res = session.post(url = url, data = jsondata, headers = headers)

    # print(res)

    response_dict = json.loads(res.text.strip())
    # print(response_dict)

    try:
        return response_dict['data'][0]['embedding']
    except:
        return []


if __name__ == "__main__":
    print(embedding("hello world"))
    print(chat([{"role": "user", "content": "hello!"}]))