from typing import List
from .tool import Tool
import re
import json
import copy
import tiktoken


# The color for intermediate result
RESET = "\033[0m"        # reset color output
GREEN = "\033[92m"       # Green text
MAGENTA = "\033[35m"     # Magenta text
RED = "\033[31m"         # Red text
BOLD = "\033[1m"         # Bold text
BLUE = "\033[34m"        # Blue text


MAX_INPUT_TOKEN = 3500


class Agent:
    """ Simple Implementation of Chain of Thought Agent
    """
    def __init__(self, llm:callable, tools:List[Tool], prompt_template:str, task:str):
            """ Intialize an agent.
            llm callable: a function which could call llm and return response
            tools List[Tool]: a list of Tool
            prompt_template str: a template for prompt, it should contain the following 3 keywords: {tool_names_and_descriptions}, {tool_names}, {agent_playground}, {task}
            """
            self.llm = llm # caller for large language model
            self.tools = tools # a List of Tool
            self.iterations = 0 # number of iterations to now
            self.prompt_template = prompt_template # template of promot, defined by user 
            self.task = task # final task
            self.finish = False # if finish the task / answer the question
            self.final_answer = "" # final answer (if applicable)
            self.tool_map = {} # a mapping from action name to action Tool object
            self.tool_names = [] # a list of tool names
            for tool in self.tools:
                self.tool_names.append(tool.tool_name)
                self.tool_map[tool.tool_name] = tool

            self.tool_names_and_descriptions = "\n".join([tool.tool_name+" - "+tool.tool_description for tool in self.tools]) # tool names and desctiptions
            
            print('='*20)
            print(self.tool_names_and_descriptions)
            print('='*20)

            self.history = [] # a list of history thoughts, actions, action_inputs, obeservations,...
            self.exception_count = 0 # count the number of exceptions
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
        available_tokens_for_agent_playground = MAX_INPUT_TOKEN - num_tokens_system

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
        
        return formatted_prompt

    def step(self):
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

            # generate response 
            response = self.llm(formatted_prompt)
            if response == "":
                continue

            print(f"Thought: {response}")
            
            if "Final Answer" in response: # in case the final answer is obtained
                print(f"{BLUE}{BOLD}Task finished!{RESET}")
                response += "\n"
                self.finish = True
                self.final_answer = response
                self.history.append(response)
                
                # extract the final answer
                pattern = r'Final Answer: (.+?)\n'
                match = re.search(pattern, response)
                if match:
                    action_content = match.group(1)
                    print(f"{BLUE}{BOLD}Final Answer: {action_content}{RESET}")
                    self.final_answer = action_content
                else:
                    print(f"{RED}{BOLD}Error: cannot find Final Answer{RESET}")

                return

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
    
    def run(self, max_step:int=10):
        """ run multiple steps until catch finish signal
        """
        # mainloop of run()
        while (not self.finish) and (self.iterations < max_step):
            self.step()
        return

