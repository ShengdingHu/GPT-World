import json
import requests
from typing import List
import os
import openai
from gptworld.utils.logging import get_logger
import time

logger = get_logger(__name__)

def chat(context, MAX_OUTPUT_TOKEN_LEN=1024,temperature=0.1,attemps=5) -> str:
    if isinstance(context, str):
        context = [{"role": "user", "content": context}]
    attempt=0
    while attempt<attemps:
        try:
            if os.environ['OPENAI_METHOD'] == "pool":
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

                try:
                    response_dict = json.loads(res.text.strip())
                except json.decoder.JSONDecodeError:
                    logger.warning("Unable to generate response")
                    return ""
                try:
                    return response_dict['choices'][0]['message']['content'].strip()
                except:
                    logger.warning(f"Unable to generate response")
                    return ""
            elif os.environ['OPENAI_METHOD'] == "api_key":
                response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=context
                        )
                try:
                    return response['choices'][0]['message']['content'].strip()
                except:
                    logger.warning("Unable to generate response")
                    return ""
        except Exception as e:
            attempt+=1
            logger.exception("Error when requesting charGPT. Retrying")
            # print(f"Error: {e}. Retrying")
            time.sleep(1)
    Warning(f'chat() failed after {attemps} attempts. returning empty response')
    return ""
        



def get_embedding(text: str,attempts=3) -> List[float]:
    # if os.environ['OPENAI_METHOD'] == 'pool':  # TODO, remove this in public ver–sion.
    attempt=0
    while attempt<attempts:
        try:
            if os.environ['OPENAI_METHOD'] == "pool":
                url = "http://freegpt.club/gptworld_embedding"
                headers={"Content-Type":"application/json"}
                session = requests.Session()
                data = {
                    "model": "text-embedding-ada-002",
                    "input": text
                }

                jsondata = json.dumps(data)
                res = session.post(url = url, data = jsondata, headers = headers)
                response_dict = json.loads(res.text.strip())
                try:
                    return response_dict['data'][0]['embedding']
                except:
                    return []
            elif os.environ['OPENAI_METHOD'] == "api_key":
                text = text.replace("\n", " ")
                embedding = openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]
                return embedding
        except Exception as e:
            attempt += 1
            logger.exception("Error when requesting charGPT. Retrying")
            # print(f"Error: {e}. Retrying")
            time.sleep(1)
    Warning(f'get_embedding() failed after {attempts} attempts. returning empty response')


if __name__ == "__main__":
    print(get_embedding("hello world"))
    print(chat([{"role": "user", "content": "hello!"}]))