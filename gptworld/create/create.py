import os
import sys
import json
from typing import List, Dict
from gptworld.create.tool_agent import as_tool # Import function decorator
from gptworld.create.tool_agent import ToolAgent # Import Agent who can use tools

# Import OpenAI language model
from gptworld.models.openai_api import chat as llm 

# Import Tokenizer for OpenAI language model
import tiktoken 
tokenizer = tiktoken.get_encoding("cl100k_base").encode

# Import named entity embedding tool
from gptworld.create.entity_embedding import make_entity_embedding

# Define prompt for environment generation agent (root agent)
ROOT_PROMPT = """You are a environment designer who can create a complete environment according to user's request in natural language using provided API functions.
The environment contains three part. 
The first part is area. such as a living home, a reading room, a kitchen, etc. 
The second part is object, like an apple tree, a car, etc. 
The third part is agent, such as a person, a cat, a dog, a policeman, etc. 
Now you are expected to configure them one by one.
If you need to build some areas with fine-grained work, you could assign sub tasks to your assistant. You can assign mulitple sub tasks, so your work will be of high quality.

Your action boundary is [top, left, bottom, right] = {action_boundary}, all locations (integers) you use could not overflow this boundary.

You now have access to the following API functions: 
{tool_names_and_descriptions}
Use the following format:
Thought: you should always think about what to do
Action: the action to take, should only be one of {tool_names}
Action Input: the input to the action, please use JSON format, if no input needed, use {{}}
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I think I have finished the given task.
Action: submit_job
Action Input: {{}}
Observation: Done!

Begin! Your TASK is: {task}
{agent_playground}
"""

# Prompt for sub agent (fine grained)
CHILD_PROMPT = """You are a environment designer who can create a complete, fine-grained environment according to user's request in natural language using provided API functions.
The environment contains three part. 
The first part is area. such as a living home, a reading room, a kitchen, etc. 
The second part is object, like an apple tree, a car, etc. 
The third part is agent, such as a person, a cat, a dog, a policeman, etc. 
Now you are expected to configure them one by one.

Your action boundary is [top, left, bottom, right] = {action_boundary}, all locations (integers) you use could not overflow this boundary.

You now have access to the following API functions: 
{tool_names_and_descriptions}
Use the following format:
Thought: you should always think about what to do
Action: the action to take, should only be one of {tool_names}
Action Input: the input to the action, please use JSON format, if no input needed, use {{}}
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I think I have finished the given task.
Action: submit_job
Action Input: {{}}
Observation: Done!

Begin! Your TASK is: {task}
{agent_playground}
"""

# Define global counters for areas, objects, and agents
num_areas = 1
num_objects = 0
num_agents = 0

# Define result global variable
result = {}
object_detailed = {}

# Define multiple APIs for environment creation
@as_tool("create_sub_task")
def create_sub_task(task: str, action_boundary: List[int]) -> str:
    """ This API allows you to assign a subtask to your helper.
    
    When you need to create multiple complex and fine grained areas, you can assign multiple sub tasks by giving a description of this specific task, and the corresponding boundary, so that a helper will help to carefully build this area for you. 
    The helper does not have any knowledge about this area, so make sure you provide specific and sufficient information about this area in your description.
    Additionally, this API could be used for multiple times. So, make good use of it.
    
    Args:
        task: str: the specific and sufficient task description, what do you want to build in this area?
        action_boundary: [top:int, left: int, bottom: int, right: int], the action boundary of this task 
    
    Returns:
        A message shows whether the task is completed.
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
    
    Args:
        name: str: the name of area, like 'Alice's home'
        area_boundary: [top:int, left: int, bottom: int, right: int], the boundary of this area
    
    Returns:
        A message shows observation.
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
        "border": 1,
    }
    result["areas"].append(area_blob)
    return f"Added area {name}"

def find_eid(c:List[int]):
    """Given a coordinate c of an object, find the first k from the back such that c is inside the rectangular region defined by k["location"], and return k["eid"]. 
    
    Args:
        c: [x: int, y:int] coordinate of objects
    
    Returns:
        environment id containing this coordinate
    """
    for k in reversed(result["areas"]):
        [[x1, y1], [x2, y2]] = k["location"]
        if x1 <= c[0] <= x2 and y1 <= c[1] <= y2:
            return k["id"]
    return ""

@as_tool("add_object")
def add_object(name: str, location: List[int], engine: str, traits: str, status: str, memory: List[str]) -> str:
    """ This API allows you to add an object to the environment.
    
    Args:
        name: str: the name of object, like 'Apple Tree'
        location: [x: int, y: int]: the location of this object
        enegine: str: either "environment" or "object". If the object is pure material such as a table, a bottle of water, use "environment", if the object can make reaction such as a TV or a car, use "object"
        traits: str: multiple adjective dexcribing the characters of this object, use comma to seperate
        status: str: the status of this object, several words described
        memory: List[str]: memory of this object, like ["I am an apple tree", "I am 10 years old", "My master is Alice", "I am a TV", "I have many apples, " ...] you can unlock your imagination to make up, expect more
    
    Returns:
        A message shows observation.
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
    detailed_blob = {
        "traits": traits,
        "name": name,
        "vision_radius": 8,
        "attention_bandwidth": 8,
        "retention": 8,
        "time": None,
        "eid": eid,
        "location": location,
        "max_velocity": "1/s",
        "moving": "false",
        "status": status,
        "memory": memory,
        "incoming_observation": []
    }
    object_detailed[object_id] = detailed_blob
    result["objects"].append(object_blob)
    return f"Added object {name}"

@as_tool("add_agent")
def add_agent(name: str, location: List[int], traits: str, status: str, age: int, max_velocity: int, plan: List[str], description: List[str]) -> str:
    """ This API allows you to add an agent to the environment.
    
    Args:
        name: str: the name of agent, like 'Bob', 'Mr. Wang', use a real name rather than 'Person 1', 'Customer 1'.
        location: [x: int, y: int]: the location of this agent
        traits: str: multiple adjective dexcribing the characters of this object, use comma to seperate
        status: str: the status of this object, several words described
        age: int: age in years
        max_velocity: int: the maximum movement velocity of this agent, by default it is 1/s for an adult
        plan: List[str]: the next things to do, for example, ['I want to visit my professor', 'I want to play GTA5', ...] expect detailed ones.
        description: List[str]: description of this agent, like ["Bob is a professor at ...", "Bob is 50 years old", "Bob loves Mary.", ...] you can unlock your imagination to make up, expect more
    
    Returns:
        A message shows observation
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
    detailed_blob = {
        "traits": traits,
        "name": name,
        "age": age,
        "retention": 8,
        "eid": eid,
        "location": location,
        "max_velocity": f"{max_velocity}/s",
        "moving": "false",
        "status": status,
        "status_duration" : 0,
        "status_start_time": None,
        "plan": plan,
        "memory": f"{name}_LTM",
        "description": description,
        "incoming_observation": []
    }
    object_detailed[agent_id] = detailed_blob
    result["objects"].append(object_blob)
    return f"Added agent {name}"

@as_tool("submit_job", tool_type="finish")
def submit_job() -> str:
    """ This API terminates the current agent
    
    Args:
        No args.
    
    Return:
        A message shows observation
    """

    return "Submitted job"

# Gather the tool to a list
root_tools = [add_area, add_object, add_agent, create_sub_task, submit_job]
child_tools = [add_area, add_object, add_agent, submit_job]

# Define main function
def create_world(name: str, task: str, size: List[int]=[400, 300], max_step: int=40, output_path: str="") -> None:
    """ Create a world using natural language instruction
    
    Args:
        name: Name of your environment
        task: Your instruction in natural language
        size: Size of your world
        max_step: Maximum actions of root agent
        output_path: Saving path of output json file
    
    Returns:
        None
    """
    global result
    
    # Initialize a dict to store all results
    result = {
        "name": name,
        "current_time": "2023-04-01T07:00:00",
        "id": "e_001",
        "size": size,
        "areas": [],
        "objects": [],
    }
    
    world_width = size[0]
    world_height = size[1]
    
    # Create an agent to finish the user's request
    agent = ToolAgent(llm=llm, 
        tokenizer=tokenizer, 
        tools=root_tools, 
        prompt_template=ROOT_PROMPT, 
        task=task,
        action_boundary=[0, 0, world_width, world_height]
    )
    
    # Run the agent
    agent.multiple_actions(max_step=max_step)
    
    # Convert result["objects"] and result["areas"] into Dict[str, Dict]
    objects_dict = {}
    areas_dict = {}
    for i in result["objects"]:
        objects_dict[i["id"]] = i
    for i in result["areas"]:
        areas_dict[i["id"]] = i
    result["objects"] = objects_dict
    result["areas"] = areas_dict
    
    # Save environment.json
    json_str = json.dumps(result, indent=4)
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    
    with open(os.path.join(output_path, 'environment.json'), 'w') as f:
        f.write(json_str)

    print(f"Successfully saved environment.json at {output_path}")
    
    # Save detailed json for each object and agent
    for key in object_detailed:
        json_str = json.dumps(object_detailed[key], indent=4)
        with open(os.path.join(output_path, f'{key}.json'), 'w') as f:
            f.write(json_str)
    
    print(f"Successfully saved detailed json for objects at {output_path}")
    
    # Make embeddings for named entities
    make_entity_embedding(output_path)
    print(f"Successfully saved named entity embedding json at {output_path}")
    
    return

if __name__ == "__main__":
    # Get user's request
    task = sys.argv[1]
    
    data = create_world(name="new_environment", task=task, size=[200, 150], max_step=40, output_path='./outputs')

    
