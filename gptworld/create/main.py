import sys
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
num_areas = 0
num_objects = 0
num_agents = 0


# Define multiple APIs for environment creation
@as_tool("create_sub_task")
def create_sub_task(task: str, action_boundary: List[int]):
    """ This API allows you to assign a subtask to your helper.
    When you need to create multiple complex and fine grained areas, you can assign multiple sub tasks by giving a description of this specific task, and the corresponding boundary, so that a helper will help to carefully build this area for you. 
    The helper does not have any knowledge about this area, so make sure you provide specific and sufficient information about this area in your description.
    Additionally, you are a chief designer, so you could create multiple sub tasks. Make good use of it! 
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
    Input:
        name: str: the name of area, like 'Alice's home'
        area_boundary: [top:int, left: int, bottom: int, right: int], the boundary of this area
    """
    global num_areas

    num_areas += 1
    return f"Added area {name}"

@as_tool("add_object")
def add_object(name: str, initial_location: List[int], memory: List[str]) -> str:
    """ This API allows you to add an object to the environment.
    Input:
        name: str: the name of object, like 'Apple Tree'
        location: [x: int, y: int]: the location of this object
        memory: List[str]: memory of this object, like ["I am an apple tree", "I am 10 years old", "My master is Alice", ...]
    """
    global num_objects
    engine = "environment"

    num_objects += 1
    return f"Added object {name}"

@as_tool("add_agent")
def add_agent(name: str, initial_location: List[int], memory: List[str]) -> str:
    """ This API allows you to add an agent to the environment.
    Input:
        name: str: the name of agent, like 'Bob'
        location: [x: int, y: int]: the location of this agent
        memory: List[str]: memory of this agent, like ["I have a family of 5", "I am 30 years old", "My name is Bob", ...]
    """
    global num_agents

    num_agents += 1
    return f"Added agent {name}"

@as_tool("submit_job", "finish")
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
        action_boundary=[0, 0, 800, 1000]
    )

    # Run the agent
    agent.multiple_actions(max_step=20)

