# import from Auto-GPT at https://github.com/Torantulino/Auto-GPT/blob/master/scripts/memory/local.py

import openai
import abc
import dataclasses
import orjson
from typing import Any, List, Optional
import numpy as np
import os
import datetime
import re
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

IMPORTANCE_PROMPT='''On the scale of 1 to 10, where 1 is purely mundane
(e.g., brushing teeth, making bed) and 10 is
extremely poignant (e.g., a break up, college
acceptance), rate the likely poignancy of the
following piece of memory.
Memory: {}
Rating: <fill in>'''

openai.api_key = "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"

def get_ada_embedding(text):
    text = text.replace("\n", " ")
    # TODO: try to use request to replace openai.Embedding.create
    embedding = openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]
    return embedding

def get_importance(text):
    prompt=IMPORTANCE_PROMPT.format(text)
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    result=completion.choices[0].message['content']
    score=int(re.findall('\s*(\d+)\s*',result)[0])
    return score


EMBED_DIM = 1536
SAVE_OPTIONS = orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_SERIALIZE_DATACLASS


def create_default_embeddings():
    return np.zeros((0, EMBED_DIM)).astype(np.float32)

def create_default_importance():
    return np.zeros((0)).astype(np.int)
@dataclasses.dataclass
class CacheContent:
    texts: List[str] = dataclasses.field(default_factory=list)
    embeddings: np.ndarray = dataclasses.field(
        default_factory=create_default_embeddings
    )
    createTime: List[datetime.datetime] = dataclasses.field(default_factory=list)
    accessTime: List[datetime.datetime] = dataclasses.field(default_factory=list)
    importance: np.ndarray = dataclasses.field(default_factory=create_default_importance)
    tags: List[List[str]] = dataclasses.field(default_factory=list)

class ReflectionMemory():
    # on load, load our database
    def __init__(self, cfg) -> None:
        self.filename = f"{cfg.memory_index}.json"
        if os.path.exists(self.filename):
            with open(self.filename, 'rb') as f:
                loaded = orjson.loads(f.read())
                self.data = CacheContent(**loaded)
                # change datetime string to datetime again
                self.data.accessTime=[datetime.datetime.strptime(a,'%Y-%m-%dT%H:%M:%S') for a in self.data.accessTime]
                self.data.createTime=[datetime.datetime.strptime(a,'%Y-%m-%dT%H:%M:%S') for a in self.data.createTime]
                self.data.importance=np.array(self.data.importance).astype(np.int)
                self.data.embeddings=np.array(self.data.embeddings).astype(np.float32)
        else:
            self.data = CacheContent()
        pass

    def add(self, text: str, time: datetime.datetime, tag: list = []):
        """
        Add text as entry. Also add creation time information, last access time information, importance
        tags: (characteristics, reflection_depth, plan, conversation summary, action observation, object status observation, self observation, etc)
        tags目前只作为分析工具，但也可以根据tag做调整。

        Args:
            text: str

        Returns: None
        """
        if 'Command Error:' in text:
            return ""
        self.data.texts.append(text)

        embedding = get_ada_embedding(text)

        vector = np.array(embedding).astype(np.float32)
        vector = vector[np.newaxis, :]
        self.data.embeddings = np.concatenate(
            [
                vector,
                self.data.embeddings,
            ],
            axis=0,
        )
        importance=np.array(get_importance(text))[np.newaxis]
        self.data.importance=np.concatenate(
            [
                importance,
                self.data.importance,
            ],
            axis=0,
        )
        self.data.createTime.append(time)
        self.data.accessTime.append(time)


        with open(self.filename, 'wb') as f:
            out = orjson.dumps(
                self.data,
                option=SAVE_OPTIONS
            )
            f.write(out)
        return text

    def clear(self) -> str:
        """
        Clears the redis server.

        Returns: A message indicating that the memory has been cleared.
        """
        self.data = CacheContent()
        return "Obliviated"

    def get(self, data: str) -> Optional[List[Any]]:
        """
        Gets top1 entry

        Args:
            data: The data to compare to.

        Returns: The most relevant data.
        """
        return self.query(data, 1)

    def query(self, text: str, k: int, curtime: datetime.datetime) -> List[Any]:
        """"
        get topk entry based on recency, relevance and importance

        Args:
            text: str
            k: int

        Returns: List[str]
        """
        simpleweights=[1.,1.,1.]

        embedding = get_ada_embedding(text)

        timediff=np.array([(curtime-a).total_seconds()//3600 for a in self.data.accessTime])
        recency=np.power(0.99,timediff)
        relevance = cosine_similarity(np.array(embedding)[np.newaxis,:],self.data.embeddings)[0]
        importance= self.data.importance/10

        score=recency*simpleweights[0]+importance*simpleweights[1]+relevance*simpleweights[2]

        top_k_indices = np.argsort(score)[-k:][::-1]
        # access them
        for i in top_k_indices:
            self.data.accessTime[i]=curtime

        return [self.data.texts[i] for i in top_k_indices]

    def reflection(self,):
        # initiate a reflection that inserts high level knowledge to memory
        pass

# test: 给定一堆记忆，进行一次query，两次reflection

class Config:
    pass

test_query='''
    Sam Moore is conversing about Isabella Rodriguez invites Sam Moore and his wife to a Valentine's Day party at Hobbs Cafe while discussing Sam's plans to run for local mayor and their shared interests in job creation, economic growth, and community development.
'''
test_query_time='2023-02-13 09:33:50:'

if __name__=='__main__':

    config=Config()
    setattr(config,'memory_index','../../module_test/test_agent_relection')
    r=ReflectionMemory(config)
    if len(r.data.texts)==0:
        with open('../../module_test/IR_characteristics.txt','r') as f:
            lines=f.readlines()
            for line in tqdm(lines):
                if line.startswith('['):
                    segs=line.strip().split(' ')
                    dt=datetime.datetime.strptime(' '.join(segs[1:3]),'%Y-%m-%d %H:%M:%S:')
                    r.add(' '.join(segs[3:]),dt)
        with open('../../module_test/IR_observations.txt','r') as f:
            lines=f.readlines()
            for line in tqdm(lines):
                if line.startswith('['):
                    segs=line.strip().split(' ')
                    dt=datetime.datetime.strptime(' '.join(segs[1:3]),'%Y-%m-%d %H:%M:%S:')
                    r.add(' '.join(segs[3:]),dt)
    texts=r.query(test_query,k=3,curtime=datetime.datetime.strptime(test_query_time,'%Y-%m-%d %H:%M:%S:'))
    r.reflection()
    r.reflection()