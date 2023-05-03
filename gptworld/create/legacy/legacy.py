from gptworld.models.openai_api import chat
import re
import json

class EnvironmentCreator:
    def __init__(self, ):
        pass
    
    def add_description(self, description):
        self.description = description
    
    def create(self,):
        object_dict = self.create_objects()
        print(object_dict)
        pass

    def create_objects(self, ):
        Prompt = """Now suppose you are a environment designer. You can use a json file to create a 2-D environment for the described scene. The environment file contains three part. The first is the area. which is the distinct function area. The second is the objects. The third is the agents. Now you are expected to configure them one by one. In this round, you only need to give me the object config. Note that **only the objects that can provide reaction (e.g., TV react to turning on) has `object` as the `engine`, other (e.g., wood) has `environment` as the `engine`. For example, the json file (omitted some keys) to describe a house with a yard, two bedroom, one for alice, and one for Bob and Carol, a living home, a reading room, a kitchen can be like the following: 

Object Config:
```json
{{
    "o_001": {{
                "id": "o_001",
                "name": "apple tree",
                "eid": "e_002",
                "location": [10, 130],
                "engine": "object"
            }},
    "o_002": {{
        "id": "o_002",
        "name": "apple tree",
        "eid": "e_002",
        "location": [20, 130],
        "engine": "object"
    }},
    "o_003": {{
        "id": "o_003",
        "name": "chair",
        "eid": "e_002",
        "location": [30, 80], 
        "engine": "environment"
    }},
    "o_004": {{
        "id": "o_004",
        "name": "sofa",
        "eid": "e_004",
        "location": [25, 45],
        "size": [10, 5],
        "engine": "environment"
    }},
    "o_005": {{
        "id": "o_005",
        "name": "television",
        "eid": "e_004",
        "location": [25, 5],
        "engine": "environment"
    }}
}}
```

Now can you give me the bject config for the following environment: {}.  You need to firstly think what are suited for objects before you give me the configs.
Use the following format
Thought: 
Object Config:

Now begin:
"""
        filled_prompt = Prompt.format(self.description)
        result = chat(filled_prompt)
        json_dict = self.extract_json(result)
        return json_dict
    
    def extract_json(self, text):
        pattern = re.compile(r'```json\s*(.*?)\s*```', re.DOTALL)
        match = pattern.search(text)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        else:
            return ''


# ...
# "objects": {{ 
#         "o_001": {{
#             "id": "o_001",
#             "name": "apple tree",
#             "eid": "e_002",
#             "location": [10, 130],
#             "engine": "object"
#         }},
#         "o_002": {{
#             "id": "o_002",
#             "name": "apple tree",
#             "eid": "e_002",
#             "location": [20, 130],
#             "engine": "object"
#         }},
#         "o_003": {{
#             "id": "o_003",
#             "name": "chair",
#             "eid": "e_002",
#             "location": [30, 80], 
#             "engine": "environment"
#         }},
# }}
# ```


        

    
    