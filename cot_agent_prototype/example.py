from .tool import as_tool
from .agent import Agent
from .prompt import TC_PROMPT

@as_tool("tool1")
def func1(arg1: int = 1, arg2: str = "hello world"):
    """ Explain the function, prompt the model to use it at proper stage
    """
    return "hi!"

@as_tool("tool2")
def func2(name: str = "Alex", address: str = "127.0.0.1"):
    """ Explain the function, prompt the model to use it at proper stage
    """
    return "bye!"

tools = [func1, func2()]

def llm(prompt):
    """ Mock large language model function
    """
    return "response"

agent = Agent(llm=llm, tools=tools, prompt_template=TC_PROMPT, task="say hello to me")

agent.run(5)

