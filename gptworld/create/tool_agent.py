from typing import List
import re
import json
import copy
import inspect


class Tool:
    """ All function will be encapulated into Tool object for convenience of all.
    This class is callable, when called, it will execute the corresponding function.
    """
    def __init__(self, func:callable, tool_name:str, tool_description:str="", tool_type:str="normal"):
        """ Store the function, description, and tool_name in a class to store the information
        """
        self.func = func
        if tool_description == "":
            self.tool_description = f"{inspect.signature(func)} : {func.__doc__}"
        else:
            self.tool_description = tool_description
        self.tool_name = tool_name
        self.tool_type = tool_type
    
    def __call__(self, *args, **kwargs):
        """ When the instance called, this method will run
        """
        return self.func(*args, **kwargs)

def as_tool(tool_name: str, tool_type: str="normal") -> Tool:
    """ Convert a function as a tool function, return a callable Tool
        Usage 1:
        @as_tool("weather")
        def get_weather_today(location: str) -> str:
            ''' get_weather_today(location: str) -> None: get today's weather forcast at given location.
            '''
            return "today is sunny!"
        Will actually yield:
        tool = Tool(get_weather_today, "weather")
        which is a callable object, when called, the original function will be called.
        Usage 2:
        @as_tool("submit_work", "finish")
        def submit_file():
            ''' if you think you have completed the task, call this function to submit your work.
            '''
            return "the work has been submitted"
        You will define this function as a finish tool, after this tool is called, the chain will temrinate.
    """
    def decorator(func: callable) -> Tool:
        """ The original decorator, return wrapper
        """
        tool = Tool(func=func, tool_name=tool_name, tool_type=tool_type)
        print(f"[system]: as tool: {tool_name}")
        return tool # return a callable class instead of a function
    return decorator # return a callable class instead of a function


# The color for intermediate result
RESET = "\033[0m"        # reset color output
GREEN = "\033[92m"       # Green text
MAGENTA = "\033[35m"     # Magenta text
RED = "\033[31m"         # Red text
BOLD = "\033[1m"         # Bold text
BLUE = "\033[34m"        # Blue text

# Maximum number of tokens of context for language model call
MAX_SHORT_TERM_MEMORY = 3500


class ToolAgent:
    """ Simple Implementation of Tool-using Agent with Chain of Thought 
    """
    def __init__(self, llm:callable, tokenizer:callable, tools:List[Tool], prompt_template:str, task:str, action_boundary:List[int]):
            """ Intialize an agent.
            
            Args:
                llm callable: a function which could call llm and return response
                tokenizer: callable, a function to tokenize natural language into tokens, should return a list of integers
                tools List[Tool]: a list of Tool
                prompt_template str: a template for prompt, it should contain the following 3 keywords: {tool_names_and_descriptions}, {tool_names}, {agent_playground}, {task}
            """
            self.llm = llm # caller for large language model
            self.tokenizer = tokenizer
            self.tools = tools # a List of Tool
            self.iterations = 0 # number of iterations to now # TODO: relation with frame?
            self.prompt_template = prompt_template # template of promot, defined by user  # TODO: load from where?
            self.task = task # final task
            self.action_boundary = action_boundary

            self.finish = False # if finish the task / answer the question
            self.final_answer = "" # final answer (if applicable)
            self.tool_map = {} # a mapping from action name to action Tool object
            self.tool_names = [] # a list of tool names

            # register tools
            for tool in self.tools:
                self.tool_names.append(tool.tool_name)
                self.tool_map[tool.tool_name] = tool

            # tool names and desctiptions
            self.tool_names_and_descriptions = "\n".join([tool.tool_name+" - "+tool.tool_description for tool in self.tools]) 
            
            # print('='*20)
            # print(self.tool_names_and_descriptions)
            # print('='*20)

            self.history = [] # a list of history thoughts, actions, action_inputs, obeservations,...
            self.exception_count = 0 # count the number of exceptions
            return
  
    def compose(self):
        """ Compose the context feed to large language model in this step (with trucation to avoid overflow of total tokens)
        """
        # Firstly, truncate

        # count system prompt length
        formatted_prompt = self.prompt_template.format(
            tool_names_and_descriptions=self.tool_names_and_descriptions, 
            tool_names=f"[{', '.join(self.tool_names)}]", 
            task=self.task, 
            action_boundary=self.action_boundary,
            agent_playground="",
        )
        
        num_tokens_system = len(self.tokenizer(formatted_prompt))
        available_tokens_for_agent_playground = MAX_SHORT_TERM_MEMORY - num_tokens_system

        # reverse self.history
        history_copy = copy.deepcopy(self.history)
        history_copy.reverse()

        # truncate agent_playground
        agent_playground = []
        num_tokens = 0
        for message in history_copy:
            length_message = len(self.tokenizer(message))
            if (num_tokens + length_message) <= available_tokens_for_agent_playground:
                num_tokens += length_message
                agent_playground.append(message)

        # reverse back
        agent_playground.reverse() # recover the original agent_playground

        # finally ground the prompt template
        formatted_prompt = self.prompt_template.format(
            tool_names_and_descriptions=self.tool_names_and_descriptions, 
            tool_names=f"[{', '.join(self.tool_names)}]", 
            task=self.task, 
            action_boundary=self.action_boundary,
            agent_playground="".join(agent_playground)
        )
        
        return formatted_prompt

    def action(self):
        """ Single action step"""

        self.iterations += 1

        # compose the context with truncation
        formatted_prompt = self.compose()

        # if exception occurs, retry 3 times at most
        num_trial = 0
        no_exception = False

        # mainloop of step()
        while (not no_exception) and (num_trial < 3):
            num_trial += 1

            # Generate response 
            # This stop token is of vital importance, if removed, this model will have hallucination.
            response = self.llm(formatted_prompt, stop=["Observation:"], temperature=0.5, MAX_OUTPUT_TOKEN_LEN=500) 
            
            if response == "":
                continue

            print(f"Thought: {response}")

            # extract the Action
            pattern = r'Action: (.+?)\n'
            match = re.search(pattern, response)
            if match:
                action_content = match.group(1)
                print(f"{GREEN}{BOLD}Action: {action_content}{RESET}")
            else:
                print(f"{RED}{BOLD}Error: cannot find Action{RESET}")
                continue
            
            # extract the Action Input
            pattern = r'Action Input:\s*(\{.*\})'
            match = re.search(pattern, response)

            if match:
                action_input_content = match.group(1)
                print(f"{GREEN}{BOLD}Action Input: {action_input_content}{RESET}")
            else:
                print(f"{RED}{BOLD}Error: cannot find Action Input{RESET}")
                continue
            
            # find the tool of action
            action_tool = self.tool_map[action_content]

            # pass the Action Input (in JSON format) to the action_tool function, get observation
            try:
                action_input_content = json.loads(action_input_content) # parse str to json
                observation = action_tool(**action_input_content)
            except Exception as e:
                print(f"{RED}{BOLD}Exception, retrying...{RESET}")
                self.exception_count += 1
                observation = e

            self.history.append(response)
            self.history.append("\n")

            print(f"{MAGENTA}{BOLD}Observation: {observation}\n{RESET}")

            self.history.append(f"Observation: {observation}\n")
            self.history.append(f"Thought: ")

            if action_tool.tool_type == "finish": 
                print(f"{BLUE}{BOLD}Task finished!{RESET}")
                self.finish = True

            no_exception = True

            # if too many exceptions 
            if self.exception_count > 10:
                self.finish = True
                print(f"{RED}{BOLD}Too many exceptions, terminated.{RESET}")
                return

        return
    
    def multiple_actions(self, max_step:int=10):
        """ run multiple steps until catch finish signal
        """
        # mainloop of run()
        while (not self.finish) and (self.iterations < max_step):
            self.action()
        return

