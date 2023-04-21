from gptworld.core.agent import GPTAgent
from datetime import datetime
import openai
import os
import json
from gptworld.models.openai import chat as request

openai.api_key = "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"
openai.api_key_path=None
openai.organization=None
os.environ['OPENAI_METHOD'] = "api_key"
## if you want to run this test, run 'query_reflection.py' first

# 科目一
file_dir='unit_test'
file_name='../static_files/test_env0/a_001r.json'
agent_path = os.path.join(file_dir, file_name)
if os.path.exists(agent_path):
    with open(os.path.join(file_dir, file_name), 'r') as f:
        data = json.load(f)
    data['Memory']='test_agent_reflection'
IRagent=GPTAgent(**{"state_dict": data, "agent_file": '../static_files/test_env0/a_001r.json','environment':None})

summary=IRagent.generate_summary(datetime.now().replace(microsecond=0))

# 科目二
# observations=request('Generate 10 random observations. ')
observations="""1. The temperature outside was 64 degrees Fahrenheit. 
2. A blue jay was spotted flying over the park. 
3. A gust of wind blew through the trees. 
4. A dog barked in the distance. 
5. A car drove by on the street. 
6. A flock of geese flew overhead. 
7. The sun shone brightly in the sky. 
8. A butterfly fluttered by. 
9. Clouds moved across the sky. 
10. A bee buzzed around a nearby flower.
""".split('\n')
for ob in observations:
    IRagent.incoming_observation.append(ob)
    IRagent.step(datetime.now().replace(microsecond=0))