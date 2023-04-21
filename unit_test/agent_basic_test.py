from gptworld.core.agent import GPTAgent
from datetime import datetime
import openai
import os
import json

openai.api_key = "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"


## if you want to run this test, run 'query_reflection.py' first

file_dir='unit_test'
file_name='../static_files/test_env0/a_001r.json'
agent_path = os.path.join(file_dir, file_name)
if os.path.exists(agent_path):
    with open(os.path.join(file_dir, file_name), 'r') as f:
        data = json.load(f)
    data['Memory']='test_agent_reflection'
IRagent=GPTAgent(**{"state_dict": data, "file_dir": file_dir})

summary=IRagent.generate_summary(datetime.now())

pass