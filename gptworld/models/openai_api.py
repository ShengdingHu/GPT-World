import json
import requests
from typing import List
import os
import openai
from gptworld.utils.logging import get_logger
import time

logger = get_logger(__name__)

def chat(context, MAX_OUTPUT_TOKEN_LEN=1024,temperature=0.1,attemps=5, stop=None) -> str:
    if isinstance(context, str):
        context = [{"role": "user", "content": context}]
    attempt=0
    while attempt<attemps:
        try:
            response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=context,
                    stop=stop,
                    )
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            attempt+=1
            logger.error(f"Error {e} when requesting charGPT. Retrying")
            # print(f"Error: {e}. Retrying")
            time.sleep(10)
    logger.warning(f'chat() failed after {attemps} attempts. returning empty response')
    return ""
        



def get_embedding(text: str,attempts=3) -> List[float]:
    # if os.environ['OPENAI_METHOD'] == 'pool':  # TODO, remove this in public ver–sion.
    attempt=0
    while attempt<attempts:
        try:
            text = text.replace("\n", " ")
            embedding = openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]
            return embedding
        except Exception as e:
            attempt += 1
            logger.error(f"Error {e} when requesting openai models. Retrying")
            time.sleep(10)
    logger.warning(f'get_embedding() failed after {attempts} attempts. returning empty response')


if __name__ == "__main__":
    print(get_embedding("hello world"))
    print(chat([{"role": "user", "content": "hello!"}]))
    print(chat([{"role": "user", "content": "hello!"}], stop=["!"]))