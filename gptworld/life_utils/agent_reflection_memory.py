# import from Auto-GPT at https://github.com/Torantulino/Auto-GPT/blob/master/scripts/memory/local.py

import openai
import dataclasses
import orjson
from typing import Any, List, Optional, Union
import numpy as np
import os
from datetime import datetime
import re
from sklearn.metrics.pairwise import cosine_similarity
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
The content or people mentioned is not real. You can hypothesis any reasonable context. \
Please strictly only output one number. \
Memory: {} \
Rating: <fill in>'''
IMMEDIACY_PROMPT = '''On the scale of 1 to 10, where 1 is requiring no short time attention\
(e.g., a bed is in the room) and 10 is \
needing quick attention or immediate response(e.g., being required a reply by others), rate the likely immediacy of the \
following statement. \
If you think it's too hard to rate it, you can give an inaccurate assessment. \
The content or people mentioned is not real. You can hypothesis any reasonable context. \
Please strictly only output one number. \
Memory: {} \
Rating: <fill in>'''
QUESTION_PROMPT = '''Given only the information above, what are 3 most salient \
high-level questions we can answer about the subjects in the statements?'''

INSIGHT_PROMPT = '''What at most 5 high-level insights can you infer from \
the above statements? Only output insights with high confidence. 
example format: insight (because of 1, 5, 3)'''





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

def get_immediacy(text):
    prompt = IMMEDIACY_PROMPT.format(text)
    result = chat(prompt)
    try:
        score = int(re.findall(r'\s*(\d+)\s*', result)[0])
    except:
        logger.warning(
                    'Abnormal result of immediacy rating \'{}\'. Setting default value'.format(result))
        score = 0
    return score


def get_questions(texts):
    prompt = '\n'.join(texts) + '\n' + QUESTION_PROMPT
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
    insights = [isg for isg in result.split('\n') if len(isg.strip())>0][:5]
    insights = ['.'.join(i.split('.')[1:]) for i in insights]
    # remove insight pointers for now
    insights = [i.split('(')[0].strip() for i in insights]
    return insights


def create_default_embeddings():
    return np.zeros((0, EMBED_DIM)).astype(np.float32)


def create_default_importance():
    return np.zeros((0)).astype(np.int32)

def create_default_immediacy():
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
    # immediacy rating given by asking LLM
    immediacy: np.ndarray = dataclasses.field(default_factory=create_default_immediacy)
    # Tags, other attributes for memory
    tags: List[List[str]] = dataclasses.field(default_factory=list)


class ReflectionMemory():
    # on load, load our database
    """
    memory_index: path for saving memory json file
    reflection_threshold: the threshold for deciding whether to do reflection

    """
    default_thres = 100

    def __init__(self, state_dict, file_dir='./', uilogging=None,clear_memory=False) -> None:
        # the least importance threshold for reflection. It seems that setting it to 0 does not induce duplicate reflections
        self.name = state_dict['name']
        self.uilogging = uilogging
        self.reflection_threshold = state_dict.get( 'reflection_threshold', self.default_thres)

        # memory_ids
        self.memory_id = state_dict.get('memory', state_dict['name']+'_LTM')
        self.base_id=state_dict.get('base',None)

        # memory_file_names
        self.filename = os.path.join(file_dir,f"{self.memory_id}.json")
        self.filename_base=os.path.join(file_dir,f"{self.base_id}.json") if self.base_id is not None else None

        # if you are really using base file, notice base should be memory before current environment running time.

        self.data=CacheContent()
        if self.filename_base is not None and os.path.exists(self.filename_base):
            self.append_from_orjson(self.filename_base)

        if os.path.exists(self.filename) and not clear_memory:
            self.append_from_orjson(self.filename)

        # members
        self.accumulated_importance = 0
        if len(self.data.importance) > 0:
            # self.sort_data_by_createtime()
            for i, tag in zip(reversed(self.data.importance), reversed(self.data.tags)):
                if 'reflection' not in tag:
                    self.accumulated_importance += i
                else:
                    break


    def append_from_orjson(self,filename):
        with open(filename, 'rb') as f:
            loaded = orjson.loads(f.read())
            jsondata = CacheContent(**loaded)
            # conversions induced by orjson
            self.data.accessTime.extend([datetime.strptime(a, '%Y-%m-%dT%H:%M:%S') for a in jsondata.accessTime])
            self.data.createTime.extend([datetime.strptime(a, '%Y-%m-%dT%H:%M:%S') for a in jsondata.createTime])
            self.data.importance = np.concatenate(
                [
                    self.data.importance,
                    np.array(jsondata.importance).astype(np.int32)
                ],
                axis=0,
            )
            self.data.immediacy = np.concatenate(
                [
                    self.data.immediacy,
                    np.array(jsondata.immediacy).astype(np.int32)
                ],
                axis=0,
            )
            self.data.embeddings = np.concatenate(
                [
                    self.data.embeddings,
                    np.array(jsondata.embeddings).astype(np.float32)
                ],
                axis=0,
            )
            self.data.texts.extend(jsondata.texts)
            self.data.tags.extend(jsondata.tags)

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
        immediacy= np.array(get_immediacy(text))[np.newaxis]
        self.data.immediacy = np.concatenate(
            [
                self.data.immediacy[:insert_point],
                immediacy,
                self.data.immediacy[insert_point:],
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
        return self.query(text, k, datetime.now())

    def query(self, text: Union[str,List[str]], k: int, curtime: datetime, nms_threshold = 0.99) -> List[Any]:
        """
        get topk entry based on recency, relevance, importance, immediacy
        The query result can be Short-term or Long-term queried result.
        formula is
        $$ score= sim(q,v) *max(LTM\_score, STM\_score) $$
        $$ STM\_score=time\_score(createTime)*immediacy $$
        $$ LTM\_score=time\_score(accessTime)*importance $$
        time score is exponential decay weight. stm decays faster.

        The query supports querying based on multiple texts and only gives non-overlapping results
        If nms_threshold is not 1, nms mechanism if activated. By default,
        use soft nms with modified iou base(score starts to decay iff cos sim is higher than this value,
         and decay weight at this value if 0. rather than 1-threshold).


        Args:
            text: str
            k: int

        Returns: List[str]
        """
        assert(len(text)>0)
        texts=[text] if isinstance(text,str) else text
        maximum_score=None
        for text in texts:
            embedding = get_embedding(text)

            accesstimediff = np.array([(curtime - a).total_seconds() // 3600 for a in self.data.accessTime])
            createtimediff = np.array([(curtime - a).total_seconds() // 60 for a in self.data.createTime])

            recency = np.power(0.99, accesstimediff)
            instant = np.power(0.90, createtimediff)


            if len(self.data.embeddings) == 0:
                return []

            relevance = cosine_similarity(np.array(embedding)[np.newaxis, :], self.data.embeddings)[0]

            importance = self.data.importance / 10
            immediacy=self.data.immediacy/10

            ltm_w=recency*importance
            stm_w=instant*immediacy
            score = relevance*np.maximum(ltm_w,stm_w)
            if maximum_score is not None:
                maximum_score=np.maximum(score,maximum_score)
            else:
                maximum_score=score

        if nms_threshold==1:
            # no nms is triggered
            top_k_indices = np.argsort(maximum_score)[-k:][::-1]
        else:
            # TODO: soft-nms
            assert(nms_threshold<1 and nms_threshold>=0)
            top_k_indices=[]
            while len(top_k_indices)<min(k,len(self.data.texts)):
                top_index=np.argmax(maximum_score)
                top_k_indices.append(top_index)
                maximum_score[top_index]=-1  # anything to prevent being chosen again
                top_embedding=self.data.embeddings[top_index]
                cos_sim=cosine_similarity(np.array(top_embedding)[np.newaxis, :], self.data.embeddings)[0]
                score_weight=np.ones_like(maximum_score)
                score_weight[cos_sim>=nms_threshold]-=(cos_sim[cos_sim>=nms_threshold]-nms_threshold)/(1-nms_threshold)
                maximum_score=maximum_score*score_weight

        # access them and refresh the access time
        for i in top_k_indices:
            self.data.accessTime[i] = curtime
        # sort them in time periods. if the data tag is 'observation', ad time info output.
        top_k_indices=sorted(top_k_indices,key=lambda k:self.data.createTime[k])
        query_results=[]
        for i in top_k_indices:
            query_result=self.data.texts[i]
            if 'observation' in self.data.tags[i]:
                query_result+='   This observation happens at {}.'.format(str(self.data.createTime[i]))
            query_results.append(query_result)
        return query_results

    def reflection(self, time: datetime):
        # initiate a reflection that inserts high level knowledge to memory
        # self.sort_data_by_createtime()
        mem_of_interest = self.data.texts[-100:]
        questions = get_questions(mem_of_interest)
        # statements = sum([self.query(q, 10, time) for q in questions], [])
        statements = self.query(questions,len(questions)*10,time)
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
            logger.debug(f"Doesn't reflect since accumulated_importance={self.accumulated_importance} < reflection_threshold={self.reflection_threshold}")
            return 'reflection reject: prevent duplicate reflecting result'
        if self.data.texts.__len__()==0:
            return 'reflection reject: no memory'
        return self.reflection(time)

    def sort_data_by_createtime(self):
        """
        If memory is normally used, it's likely almost sorted.
        """
        pass
