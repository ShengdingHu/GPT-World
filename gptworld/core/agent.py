from typing import List
import re
import json
import copy
from typing import Dict
from gptworld.core.environment import Environment
import tiktoken


"""
Agent class implements the static, mind, inner, and cognitive process
"""


# The color for intermediate result
RESET = "\033[0m"        # reset color output
GREEN = "\033[92m"       # Green text
MAGENTA = "\033[35m"     # Magenta text
RED = "\033[31m"         # Red text
BOLD = "\033[1m"         # Bold text
BLUE = "\033[34m"        # Blue text


MAX_SHORT_TERM_MEMORY = 1500
MAX_LONG_TERM_MEMORY = 1500


class Agent:
    """ Simple Implementation of Chain of Thought & Task Based Agent
    """
    def __init__(self, state_dict: Dict, llm: callable, tools: List[Tool], prompt_template: str):
            """ Intialize an agent.
            state_dict: Dict -> a state dict which contains all the information about the agent
            llm: callable -> a function which could call llm and return response
            tools: List[Tool] -> a list of Tool
            prompt_template: str -> a template for prompt
            """
            
            # TODO: Note that we hope that it can maintain the tool using ability...

            # Type of the agent, either 'objective' or 'subjective'
            self.type = state_dict.get("type", None)

            # Initialized at mount time
            self.environment = None
            self.environment_id = None

            # The thinking kernel
            self.llm = llm

            #  a List of Tool
            self.tools = tools 

            self.iterations = 0 # number of iterations to now

            self.prompt_template = prompt_template # template of promot, defined by user 

            self.tool_map = {} # a mapping from action name to action Tool object
            self.tool_names = [] # a list of tool names
            for tool in self.tools:
                self.tool_names.append(tool.tool_name)
                self.tool_map[tool.tool_name] = tool

            self.tool_names_and_descriptions = "\n".join([tool.tool_name+" - "+tool.tool_description for tool in self.tools]) # tool names and desctiptions
            
            # TODO: Design details about hierachical task queue
            self.tasks = state_dict.get("tasks", {})

            # TODO: Design details about short term memory management, a list of history thoughts, actions, action_inputs, obeservations,...
            self.short_term_memory = state_dict.get("short_term_memory", [])

            # TODO: Design details about long term memory in a form of Embedding Vector : Memory Content
            self.long_term_memory = state_dict.get("long_term_memory", {})

            # TODO: Location
            self.location = state_dict.get("location", None)

            # TODO: interaction queue
            self.interaction_queue = []

            return
    
    def observe(self):
        """ update observation of around environment
        """
        # TODO: maybe need to polish a little bit: 博凯
        self.observation = self.environment.get_neighbor_environment(self.location)
        return

    def reflect(self):
        """ 每过一段时间反思当前短期记忆与Observation, 存入长期记忆
        """
        # TODO: implement reflect: 凡哥、京伟
        return
    
    def plan(self):
        """ 计划接下来的任务
        """
        # TODO: implement plan : 凡哥、京伟
        return
    
    def reprioritize(agent: Agent, **kwargs):
        """ Reprioritize task queue
        """
        # TODO: implement reprioritize : 凡哥、京伟
        return
  
    def compose(self):
        """ Compose the context feed to large language model in this step (with trucation to avoid overflow of total tokens)
        """
        # first truncation
        tokenizer = tiktoken.get_encoding("cl100k_base")

        # count system prompt length
        formatted_prompt = self.prompt_template.format(
            tool_names_and_descriptions=self.tool_names_and_descriptions, 
            tool_names=f"[{', '.join(self.tool_names)}]", 
            task=self.task, 
            agent_playground=""
        )
        
        num_tokens_system = len(tokenizer.encode(formatted_prompt))
        available_tokens_for_agent_playground = MAX_SHORT_TERM_MEMORY - num_tokens_system

        # reverse self.history
        history_copy = copy.deepcopy(self.history)
        history_copy.reverse()

        # truncate agent_playground
        agent_playground = []
        num_tokens = 0
        for message in history_copy:
            length_message = len(tokenizer.encode(message))
            if (num_tokens + length_message + 4) <= available_tokens_for_agent_playground:
                num_tokens += 4
                num_tokens += length_message
                agent_playground.append(message)

        # reverse back
        agent_playground.reverse() # recover the original agent_playground

        # finally ground the prompt template
        formatted_prompt = self.prompt_template.format(
            tool_names_and_descriptions=self.tool_names_and_descriptions, 
            tool_names=f"[{', '.join(self.tool_names)}]", 
            task=self.task, 
            agent_playground="".join(agent_playground)
        )

        #TODO: Use all the short term context to compute semnatic embedding -> use cosine similarity to compute the most relevant items and append them to the context

        # MAX_LONG_TERM_MEMORY
        
        return formatted_prompt

    def action(self):
        """ Single action step"""

        # First update the observation
        self.observe()

        # compose the context with truncation
        formatted_prompt = self.compose()

        # if exception occurs, retry 3 times at most
        num_trial = 0
        no_exception = False

        # mainloop of step()
        while (not no_exception) and (num_trial < 3):
            num_trial += 1

            # generate response
            response = self.llm(formatted_prompt)
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

            # TODO: this is legacy, maybe we need to modify this
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

            # TODO: this is a legacy, need to be adapted 
            # pass the Action Input (in JSON format) to the action_tool function, get observation
            try:
                action_input_content = json.loads(action_input_content) # parse str to json

                # TODO: use tools, need to be adapted
                action_input_content["environment"] = self.environment
                action_input_content["agent"] = self

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


if __name__ == "__main__":
    agent = Agent(llm=None, tools=[reprioritize, plan, interact, reflect], prompt_template=None, environment=None)
    agent.action()
    