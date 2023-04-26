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
import bisect
from gptworld.models.openai_api import get_embedding, chat
import gptworld.utils.logging as logging
logger = logging.get_logger(__name__)

EMBED_DIM = 1536
SAVE_OPTIONS = orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_SERIALIZE_DATACLASS | orjson.OPT_INDENT_2

IMPORTANCE_PROMPT = '''On the scale of 1 to 10, where 1 is purely mundane \
(e.g., brushing teeth, making bed) and 10 is \
extremely poignant (e.g., a break up, college \
acceptance), rate the likely poignancy of the \
following piece of memory. \
If you think it's too hard to rate it, you can give an inaccurate assessment. \
The content or people mentioned is not real. They don't have real memory context. \
Please strictly only output one number\
Memory: {} \
Rating: <fill in>'''
QUESTION_PROMPT = '''Given only the information above, what are 3 most salient \
high-level questions we can answer about the subjects in the statements?'''

INSIGHT_PROMPT = '''What 5 high-level insights can you infer from \
the above statements? (example format: insight \
(because of 1, 5, 3))'''





def get_importance(text):
    prompt = IMPORTANCE_PROMPT.format(text)
    result = chat(prompt)

    try:
        score = int(re.findall(r'\s*(\d+)\s*', result)[0])
    except:
        logger.warning(
                    'Abnormal result of importance rating \'{}\'. Setting default value'.format(result))
        score = 0
    return score


def get_questions(texts):
    prompt = '\n'.join(texts) + '\n' + QUESTION_PROMPT
    # completion = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {"role": "user", "content": prompt}
    #     ]
    # )
    result = chat(prompt)
    questions = [q for q in result.split('\n') if len(q.strip())>0]
    questions=questions[:3]
    return questions


def get_insights(statements):
    prompt = ''
    for i, st in enumerate(statements):
        prompt += (str(i + 1) + '. ' + st + '\n')
    prompt += INSIGHT_PROMPT
    result = chat(prompt)
    insights = result.split('\n')[:5]
    insights = ['.'.join(i.split('.')[1:]) for i in insights]
    # remove insight pointers for now
    insights = [i.split('(')[0].strip() for i in insights]
    return insights


def create_default_embeddings():
    return np.zeros((0, EMBED_DIM)).astype(np.float32)


def create_default_importance():
    return np.zeros((0)).astype(np.int32)


@dataclasses.dataclass
class CacheContent:
    # Natural language description of memory
    texts: List[str] = dataclasses.field(default_factory=list)
    # openAI embedding
    embeddings: np.ndarray = dataclasses.field(
        default_factory=create_default_embeddings
    )
    # create time
    createTime: List[datetime] = dataclasses.field(default_factory=list)
    # last access time
    accessTime: List[datetime] = dataclasses.field(default_factory=list)
    # importance rating given by asking LLM
    importance: np.ndarray = dataclasses.field(default_factory=create_default_importance)
    # Tags, other attributes for memory
    tags: List[List[str]] = dataclasses.field(default_factory=list)


class ReflectionMemory():
    # on load, load our database
    """
    memory_index: path for saving memory json file
    reflection_threshold: the threshold for deciding whether to do reflection

    """

    def __init__(self, state_dict, file_dir='./', uilogging=None) -> None:
        # the least importance threshold for reflection. It seems that setting it to 0 does not induce duplicate reflections
        self.name = state_dict['name']
        self.uilogging = uilogging
        self.reflection_threshold = state_dict.get( 'reflection_threshold', 0)
        self.memory_id = state_dict.get('memory', state_dict['name']+'_LTM')
        self.filename = os.path.join(file_dir,f"{self.memory_id}.json")
        if os.path.exists(self.filename):
            with open(self.filename, 'rb') as f:
                loaded = orjson.loads(f.read())
                self.data = CacheContent(**loaded)
                # conversions induced by orjson
                self.data.accessTime = [datetime.strptime(a, '%Y-%m-%dT%H:%M:%S') for a in self.data.accessTime]
                self.data.createTime = [datetime.strptime(a, '%Y-%m-%dT%H:%M:%S') for a in self.data.createTime]
                self.data.importance = np.array(self.data.importance).astype(np.int32)
                self.data.embeddings = np.array(self.data.embeddings).astype(np.float32)
        else:
            self.data = CacheContent()

        # members
        self.accumulated_importance = 0
        if len(self.data.importance) > 0:
            # self.sort_data_by_createtime()
            for i, tag in zip(reversed(self.data.importance), reversed(self.data.tags)):
                if 'reflection' not in tag:
                    self.accumulated_importance += i
                else:
                    break

    def add(self, text: str, time: datetime, tag: list = [], repeat_ok: bool = True):
        """
        Add text as entry. Also add creation time information, last access time information, importance
        It's supposed that all memory are added with non-decreasing time. The time relevant operations such as getting recent memories during reflection does not check time order.
        This kind of retrieval based memory system is vulnerable to duplicate memories, making top-k retrival giving less meaningful results. Be cautious!

        tags: (characteristics, reflection_depth, plan, conversation summary, action observation, object status observation, self observation, etc)
        tags目前只作为分析工具，但也可以根据tag做调整。


        Returns: None
        """

        if not repeat_ok and self.check_repeat(text, time):
            return

        insert_point=len(self.data.texts)
        if len(self.data.createTime)>0 and time<self.data.createTime[-1]:
            logger.warning('Wrong memory order :{} {}'.format(time,text))
            insert_point=bisect.bisect_left(self.data.createTime, time)

        self.data.texts.insert(insert_point,text)

        embedding = get_embedding(text)

        vector = np.array(embedding).astype(np.float32)
        vector = vector[np.newaxis, :]
        self.data.embeddings = np.concatenate(
            [
                self.data.embeddings[:insert_point],
                vector,
                self.data.embeddings[insert_point:],
            ],
            axis=0,
        )
        importance = np.array(get_importance(text))[np.newaxis]
        self.data.importance = np.concatenate(
            [
                self.data.importance[:insert_point],
                importance,
                self.data.importance[insert_point:],
            ],
            axis=0,
        )
        self.data.createTime.insert(insert_point,time)
        self.data.accessTime.insert(insert_point,time)
        self.data.tags.insert(insert_point,tag)
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
        """
        get topk entry based on recency, relevance and importance
        weights can be changed.


        Args:
            text: str
            k: int

        Returns: List[str]
        """
        embedding = get_embedding(text)

        timediff = np.array([(curtime - a).total_seconds() // 3600 for a in self.data.accessTime])
        recency = np.power(0.99, timediff)
        # logging.info(self.data.embeddings)
        # logging.info(np.array(embedding)[np.newaxis, :])

        if len(self.data.embeddings) == 0:
            return []

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
        # self.sort_data_by_createtime()
        mem_of_interest = self.data.texts[-100:]
        questions = get_questions(mem_of_interest)
        statements = sum([self.query(q, 5, time) for q in questions], [])
        insights = get_insights(statements)
        self.uilogging(self.name, f"Insights: {insights}")
        for insight in insights:
            self.add(insight, time, tag=['reflection'])
        return insights

    def accumulate_importance(self, importance, tag):
        if 'reflection' in tag:
            self.accumulated_importance = 0
        else:
            self.accumulated_importance += importance

    def should_reflect(self):
        return self.accumulated_importance >= self.reflection_threshold

    def maybe_reflect(self, time: datetime):
        if not self.should_reflect():
            return 'reflection reject: prevent duplicate reflecting result'
        if self.data.texts.__len__()==0:
            return 'reflection reject: no memory'
        return self.reflection(time)

    def sort_data_by_createtime(self):
        """
        If memory is normally used, it's likely almost sorted.
        """
        pass
