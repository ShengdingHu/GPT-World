import sys
import json
from typing import List
from gptworld.create.tool import as_tool # Import function decorator
from gptworld.create.tool_agent import ToolAgent # Import Agent who can use tools
from gptworld.create.prompt import ROOT_PROMPT, CHILD_PROMPT # Prompt for root agent

# Import OpenAI language model
from gptworld.models.openai_api import chat as llm 

# Import Tokenizer for OpenAI language model
import tiktoken 
tokenizer = tiktoken.get_encoding("cl100k_base").encode

# Define global counters for areas, objects, and agents
num_areas = 1
num_objects = 0
num_agents = 0


# Initialize a dict to store all results
result = {
    "name": "root",
    "current_time": "2023-04-01T07:00:00",
    "id": "e_001",
    "size": ["200", "150"],
    "areas": [],
    "objects": [],
}


# Define multiple APIs for environment creation
@as_tool("create_sub_task")
def create_sub_task(task: str, action_boundary: List[int]):
    """ This API allows you to assign a subtask to your helper.
    When you need to create multiple complex and fine grained areas, you can assign multiple sub tasks by giving a description of this specific task, and the corresponding boundary, so that a helper will help to carefully build this area for you. 
    The helper does not have any knowledge about this area, so make sure you provide specific and sufficient information about this area in your description.
    Additionally, this API could be used for multiple times. So, make good use of it.
    Input:
        task: str: the specific and sufficient task description, what do you want to build in this area?
        action_boundary: [top:int, left: int, bottom: int, right: int], the action boundary of this task 
    """
    subagent = ToolAgent(llm=llm, 
        tokenizer=tokenizer, 
        tools=child_tools, 
        prompt_template=CHILD_PROMPT, 
        task=task, 
        action_boundary=action_boundary
    )
    subagent.multiple_actions(max_step=10)
    return "Subtask finished."

@as_tool("add_area")
def add_area(name: str, area_boundary: List[int]) -> str:
    """ This API allows you to add an object to the environment. 
    Note that new area could not overlap with existing areas, so pay attention to the area_boundary.
    The areas should be evenly distributed with proper size, don't be too small or too large.
    Input:
        name: str: the name of area, like 'Alice's home'
        area_boundary: [top:int, left: int, bottom: int, right: int], the boundary of this area
    """
    global num_areas
    num_areas += 1
    area_id = "e_" + "{:03d}".format(num_areas)
    location = [
        [area_boundary[0], area_boundary[1]],
        [area_boundary[2], area_boundary[3]]
    ]
    area_blob = {
        "name": name,
        "id": area_id, 
        "location": location,
    }
    result["areas"].append(area_blob)
    return f"Added area {name}"

def find_eid(c:List[int]):
    """
    Given a coordinate c of an object, find the first k from the back such that c is inside the rectangular region defined by k["location"], and return k["eid"]. 
    Input:
        c: [x: int, y:int] coordinate of objects
    """

    for k in reversed(result["areas"]):
        [[x1, y1], [x2, y2]] = k["location"]
        if x1 <= c[0] <= x2 and y1 <= c[1] <= y2:
            return k["id"]
    return ""

@as_tool("add_object")
def add_object(name: str, location: List[int], engine: str, memory: List[str]) -> str:
    """ This API allows you to add an object to the environment.
    Input:
        name: str: the name of object, like 'Apple Tree'
        location: [x: int, y: int]: the location of this object
        enegine: str: either "environment" or "object". If the object is pure material such as a table, a bottle of water, use "environment", if the object can make reaction such as a TV or a car, use "object"
        memory: List[str]: memory of this object, like ["I am an apple tree", "I am 10 years old", "My master is Alice", ...]
    """

    global num_objects
    num_objects += 1
    object_id = "o_" + "{:03d}".format(num_objects)
    eid = find_eid(location)
    object_blob = {
        "name": name,
        "id": object_id, 
        "location": location,
        "engine": engine,
        "eid": eid
    }
    result["objects"].append(object_blob)
    return f"Added object {name}"

@as_tool("add_agent")
def add_agent(name: str, location: List[int], memory: List[str]) -> str:
    """ This API allows you to add an agent to the environment.
    Input:
        name: str: the name of agent, like 'Bob', it is suggested to name every agent rather than call he/she/it using a code.
        location: [x: int, y: int]: the location of this agent
        memory: List[str]: memory of this agent, like ["I have a family of 5", "I am 30 years old", "My name is Bob", ...]
    """
    global num_agents
    num_agents += 1
    agent_id = "a_" + "{:03d}".format(num_agents)
    eid = find_eid(location)
    object_blob = {
        "name": name,
        "id": agent_id, 
        "location": location,
        "eid": eid
    }
    result["objects"].append(object_blob)
    return f"Added agent {name}"

@as_tool("submit_job", tool_type="finish")
def submit_job() -> str:
    """ This API allows you to add an agent to the environment.
    Input:
        No input.
    """

    return "Submitted job"

# Gather the tool to a list
root_tools = [add_area, add_object, add_agent, create_sub_task, submit_job]
child_tools = [add_area, add_object, add_agent, submit_job]


if __name__ == "__main__":
    # Get user's request
    task = sys.argv[1] 

    # Create an agent to finish the user's request
    agent = ToolAgent(llm=llm, 
        tokenizer=tokenizer, 
        tools=root_tools, 
        prompt_template=ROOT_PROMPT, 
        task=task,
        action_boundary=[0, 0, 200, 150]
    )

    # Run the agent
    agent.multiple_actions(max_step=20)

    # Convert result["objects"] and result["areas"] into Dict[str, Dict]
    objects_dict = {}
    areas_dict = {}
    for i in result["objects"]:
        objects_dict[i["id"]] = i
    for i in result["areas"]:
        areas_dict[i["id"]] = i
    result["objects"] = objects_dict
    result["areas"] = areas_dict

    json_str = json.dumps(result, indent=4)
    with open('./outputs/environment.json', 'w') as f:
        f.write(json_str)

    
