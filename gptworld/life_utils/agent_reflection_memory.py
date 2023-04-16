# import from Auto-GPT at https://github.com/Torantulino/Auto-GPT/blob/master/scripts/memory/local.py

import openai
import dataclasses
import orjson
from typing import Any, List, Optional
import numpy as np
import os
from datetime import datetime
import re
from sklearn.metrics.pairwise import cosine_similarity
import logging

IMPORTANCE_PROMPT = '''On the scale of 1 to 10, where 1 is purely mundane \
(e.g., brushing teeth, making bed) and 10 is \
extremely poignant (e.g., a break up, college \
acceptance), rate the likely poignancy of the \
following piece of memory. \
Memory: {} \
Rating: <fill in>'''
QUESTION_PROMPT = '''Given only the information above, what are 3 most salient \
high-level questions we can answer about the subjects in the statements?'''

INSIGHT_PROMPT = '''What 5 high-level insights can you infer from \
the above statements? (example format: insight \
(because of 1, 5, 3))'''


def get_ada_embedding(text):
    text = text.replace("\n", " ")
    embedding = openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]
    return embedding


def get_importance(text):
    prompt = IMPORTANCE_PROMPT.format(text)
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.
    )
    result = completion.choices[0].message['content']
    try:
        score = int(re.findall(r'\s*(\d+)\s*', result)[0])
    except:
        logging.log(logging.WARNING,
                    'Abnormal result of importance rating \'{}\'. Setting default value'.format(result))
        score = 0
    return score


def get_questions(texts):
    prompt = '\n'.join(texts) + '\n' + QUESTION_PROMPT
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    result = completion.choices[0].message['content']
    questions = result.split('\n')[:3]
    return questions


def get_insights(statements):
    prompt = ''
    for i, st in enumerate(statements):
        prompt += (str(i + 1) + '. ' + st + '\n')
    prompt += INSIGHT_PROMPT
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    result = completion.choices[0].message['content']
    insights = result.split('\n')[:5]
    insights = ['.'.join(i.split('.')[1:]) for i in insights]
    # remove insight pointers for now
    insights = [i.split('(')[0] for i in insights]
    return insights


EMBED_DIM = 1536
SAVE_OPTIONS = orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_SERIALIZE_DATACLASS


def create_default_embeddings():
    return np.zeros((0, EMBED_DIM)).astype(np.float32)


def create_default_importance():
    return np.zeros((0)).astype(np.int32)


@dataclasses.dataclass
class CacheContent:
    texts: List[str] = dataclasses.field(default_factory=list)
    embeddings: np.ndarray = dataclasses.field(
        default_factory=create_default_embeddings
    )
    createTime: List[datetime] = dataclasses.field(default_factory=list)
    accessTime: List[datetime] = dataclasses.field(default_factory=list)
    importance: np.ndarray = dataclasses.field(default_factory=create_default_importance)
    tags: List[List[str]] = dataclasses.field(default_factory=list)


class ReflectionMemory():
    # on load, load our database
    """
    memory_index: path for saving memory json file
    reflection_threshold: the threshold for deciding whether to do reflection

    """

    def __init__(self, cfg) -> None:
        self.reflection_threshold = getattr(cfg, 'reflection_threshold', 10)
        self.memory_index=getattr(cfg,'memory_index','default_memory')
        self.filename = f"{self.memory_index}.json"
        if os.path.exists(self.filename):
            with open(self.filename, 'rb') as f:
                loaded = orjson.loads(f.read())
                self.data = CacheContent(**loaded)
                # change datetime string to datetime again
                self.data.accessTime = [datetime.strptime(a, '%Y-%m-%dT%H:%M:%S') for a in self.data.accessTime]
                self.data.createTime = [datetime.strptime(a, '%Y-%m-%dT%H:%M:%S') for a in self.data.createTime]
                self.data.importance = np.array(self.data.importance).astype(np.int32)
                self.data.embeddings = np.array(self.data.embeddings).astype(np.float32)
        else:
            self.data = CacheContent()

        # members
        self.accumulated_importance = 0


    def add(self, text: str, time: datetime, tag: list = [], repeat_ok: bool = True):
        """
        Add text as entry. Also add creation time information, last access time information, importance
        It's supposed that all memory are added with non-decreasing time. The time relevant operations such as getting recent memories during reflection does not check time order.

        tags: (characteristics, reflection_depth, plan, conversation summary, action observation, object status observation, self observation, etc)
        tags目前只作为分析工具，但也可以根据tag做调整。


        Returns: None
        """

        if not repeat_ok and self.check_repeat(text, time):
            return

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
        importance = np.array(get_importance(text))[np.newaxis]
        self.data.importance = np.concatenate(
            [
                importance,
                self.data.importance,
            ],
            axis=0,
        )
        self.data.createTime.append(time)
        self.data.accessTime.append(time)
        self.data.tags.append(tag)
        self.accumulate_importance(importance, tag)

        with open(self.filename, 'wb') as f:
            out = orjson.dumps(
                self.data,
                option=SAVE_OPTIONS
            )
            f.write(out)
        return text

    def check_repeat(self, text: str, time: datetime):
        for te, ti in zip(self.data.texts, self.data.createTime):
            if text == te and time == ti:
                return True
        return False

    def clear(self):
        """
        Clears the redis server.

        Returns: A message indicating that the memory has been cleared.
        """
        self.data = CacheContent()

    def get(self, text: str, k: int = 1) -> Optional[List[Any]]:
        """
        Gets the data from the memory that is most relevant to the given data.

        """
        return self.query(text, k, datetime.now(), weights=[0, 1, 0])

    def query(self, text: str, k: int, curtime: datetime, weights=[1., 1., 1.]) -> List[Any]:
        """"
        get topk entry based on recency, relevance and importance
        weights can be changed.


        Args:
            text: str
            k: int

        Returns: List[str]
        """

        embedding = get_ada_embedding(text)

        timediff = np.array([(curtime - a).total_seconds() // 3600 for a in self.data.accessTime])
        recency = np.power(0.99, timediff)
        relevance = cosine_similarity(np.array(embedding)[np.newaxis, :], self.data.embeddings)[0]
        importance = self.data.importance / 10

        score = recency * weights[0] + importance * weights[1] + relevance * weights[2]

        top_k_indices = np.argsort(score)[-k:][::-1]
        # access them
        for i in top_k_indices:
            self.data.accessTime[i] = curtime

        return [self.data.texts[i] for i in top_k_indices]

    def reflection(self, time: datetime):
        # initiate a reflection that inserts high level knowledge to memory
        mem_of_interest = self.data.texts[-100:]
        questions = get_questions(mem_of_interest)
        statements = sum([self.query(q, 5, time) for q in questions], [])
        insights = get_insights(statements)
        for insight in insights:
            self.add(insight, time, tag=['reflection'])

    def accumulate_importance(self, importance, tag):
        if 'reflection' in tag:
            self.accumulated_importance = 0
        else:
            self.accumulated_importance += importance

    def should_reflect(self):
        return self.accumulated_importance >= self.reflection_threshold

    def maybe_reflect(self, time: datetime):
        if self.should_reflect():
            self.reflection(time)
