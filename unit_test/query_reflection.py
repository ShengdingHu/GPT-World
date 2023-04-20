import openai
import abc
import dataclasses
import orjson
from typing import Any, List, Optional
import numpy as np
import os
from  datetime import datetime
import re
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
from gptworld.life_utils.agent_reflection_memory import ReflectionMemory

# test: 给定一堆记忆，进行一次query，两次reflection,
class Config:
    pass

test_query='''
    Sam Moore is conversing about Isabella Rodriguez invites Sam Moore and his wife to a Valentine's Day party at Hobbs Cafe while discussing Sam's plans to run for local mayor and their shared interests in job creation, economic growth, and community development.
'''
test_query_time='2023-02-13 09:33:50:'

openai.api_key = "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"


if __name__=='__main__':

    config=Config()
    setattr(config,'memory_index','test_agent_relection')
    r=ReflectionMemory(config)
    with open('IR_characteristics.txt','r') as f:
        lines=f.readlines()
        for line in tqdm(lines):
            if line.startswith('['):
                segs=line.strip().split(' ')
                dt=datetime.strptime(' '.join(segs[1:3]),'%Y-%m-%d %H:%M:%S:')
                text=' '.join(segs[3:])
                if text.find("This is Isabella Rodriguez's plan"):
                    tag='plan'
                else:
                    tag='characteristics'
                r.add(text,dt,[tag],False)
    with open('IR_observations.txt','r') as f:
        lines=f.readlines()
        for line in tqdm(lines):
            if line.startswith('['):
                segs=line.strip().split(' ')
                dt=datetime.strptime(' '.join(segs[1:3]),'%Y-%m-%d %H:%M:%S:')
                r.add(' '.join(segs[3:]),dt,[],False)
    texts=r.query(test_query,k=3,curtime=datetime.strptime(test_query_time,'%Y-%m-%d %H:%M:%S:'))
    print(test_query)
    print(texts)
    print(r.maybe_reflect(datetime.strptime(test_query_time,'%Y-%m-%d %H:%M:%S:')))
    print(r.maybe_reflect(datetime.strptime(test_query_time,'%Y-%m-%d %H:%M:%S:')))