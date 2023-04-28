from gptworld.models.openai_api import chat

class EnvironmentCreator:
    def __init__(self, ):
        pass
    
    def add_description(self, description):
        self.description = description
    
    def create(self,):
        Prompt = """Now suppose you are a environment designer. You can use a json file to create a 2-D environment for the described scene. The environment file contains three part. The first is the area. which is the distinct function area. The second is the objects. The third is the agents. Now you are expected to configure them one by one. In this round, you only need to give me the area config and the object config. Note that **There will be wall that separate each area**, so be careful to set the areas.  Some simple environment may only have e_001 area. For example, the json file (omitted some keys) to describe a house with a yard, two bedroom, one for alice, and one for Bob and Carol, a living home, a reading room, a kitchen can be like the following: Area Config

Area Config:
```json
{{
    "e_002": {{
    "location": [
        [
            1,
            1
        ],
        [
            80,
            150
        ]
    ],
    "name": "yard",
    "id": "e_002",
    "border": 1,
    "color": "0x228B22"
    }}
}}
```
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
        "engine": "object"
    }}
}}
```

Now can you give me the area config and objects for the following environment: {}. The same thing shouldn't be both in area and object config. They should only appear once. You need to firstly think what should be allocated to area config and what are better suited for objects before you give me the configs.
Now begin your thought first.
"""
        filled_prompt = Prompt.format(self.description)
        result = chat(filled_prompt)
        print(result)



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


        

    
    