from typing import List
import re
import json
import copy
from typing import Dict
from gptworld.core.environment import Environment
import tiktoken
import logging
import datetime

from gptworld.utils import request_GPT

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

            # The chain of thought prompt
            self.prompt_template = prompt_template # template of promot, defined by user 

            # A List of Tool
            self.tools = tools 

            # Mapping from action name to action Tool object
            self.tool_map = {} 
            self.tool_names = []
            for tool in self.tools:
                self.tool_names.append(tool.tool_name)
                self.tool_map[tool.tool_name] = tool

            self.tool_names_and_descriptions = "\n".join([tool.tool_name+" - "+tool.tool_description for tool in self.tools]) # tool names and desctiptions
            
            # TODO: Design details about hierachical task list
            self.tasks = state_dict.get("tasks", [])

            # TODO: Design details about short term memory management, a list of history thoughts, actions, action_inputs, obeservations,...
            self.short_term_memory = state_dict.get("short_term_memory", [])

            # TODO: Design details about long term memory in a form of Embedding Vector : Memory Content
            self.long_term_memory = state_dict.get("long_term_memory", {})

            # Location
            self.location = state_dict.get("location", None)

            # Interaction queue will maintain a queue of interactions
            self.interaction_queue = state_dict.get("interaction_queue", [])

            # The observation result will be stored in this variable
            self.obervation = state_dict.get("obervation", [])

            # TODO: Whether the agent is moving ("moving" or "static")
            self.movement = state_dict.get("movement", "static")

            # TODO: Maximum velocity
            self.max_velocity = state_dict.get("movement", 1)

            # The actual velocity
            self.velocity = 0

            # Child agent (something append to self)
            self.child = state_dict.get("child_agent", [])

            # Money
            self.money = state_dict.get("money", 100)

            # Mental state score, from 0 to 100
            self.mental_score = 50

            # Energetic score, from 0 to 100
            self.energetic_score = 100

            return
    
    def observe(self):
        """ Update observation of around environment
        """
        # TODO: maybe need to polish a little bit: 博凯
        self.observation = self.environment.get_neighbor_environment(self.location)
        return

    def reflect(self):
        """ Reflect the short term memory and store it into long term memory
        """
        # TODO: implement reflect: 凡哥、京伟
        return

    def generate_summary(agent):
        """

        :param agent:
        :return: summary string
        """

        retrieved_record = """
        Chris is a undergraduate student in Tsinghua University, Love to play tennis and expand knowledge on 
        many different regions. Major in Electrical Engineering, but join in the Natural Language Processing Research Team
        , very busy at his schoolwork.
        """

        query1 = f"""
        How would one describe {agent.Name}'s core characteristics given the following statements?
        {retrieved_record}
        """
        result1 = request_GPT.request(query1)

        query2 = f"""
        What is {agent.Name}'s current occupation given the following statements?
        {retrieved_record}
        """

        result2 = request_GPT.request(query2)

        query3 = f"""
        What might be {agent.Name}'s feeling about his recent progress in life given the following statements?
        {retrieved_record}
        """

        result3 = request_GPT.request(query3)

        return result1 + result2 + result3

    def plan_in_broad_strokes(agent, date: datetime.date) -> list[dict]:
        """
        broad strokes planning of an agent
        :param agent: agent object
        :param date: str representing the current day
        :return: plans, each element is a plan
                 "task", "start time": datetime.datetime, "end time":datetime.datetime
        """

        text_base = f"""
        Name:{agent.Name} (age: {agent.Age})
        Innate traits: {agent.Personality}
        {agent.Summarize}
        {agent.Memory}
        Today is {date}. Here is {agent.Name}’s plan date in broad strokes:
        [Example format: 
         1) wake up and complete the morning routine at 8:00am,
         2) go to Oak Hill College to take classes from 10:00am to 12:00pm]

        """

        request_result = request_GPT.request(text_base)

        # a typical example to test the regex expressions without access to the GPT
        # request_result = """
        # 1) Wake up at 8:00am and have breakfast,
        # 2) Go to the library to do some research from 10:00am to 12:00pm,
        # 3) Have lunch at 12:30pm,
        # 4) Play tennis from 2:00pm to 4:00pm,
        # 5) Go back to the library to do research from 4:30pm to 6:30pm,
        # 6) Have dinner at 7:00pm,
        # 7) Relax and watch a movie from 8:00pm to 10:00pm.
        # """

        logging.info(f"Request GPT result(Broad strokes):\n{request_result}")

        pattern = r"(?:\d+\))((.+) (from|at) ((?:\d+:\d+)\s*(?:am|pm))(?: to ((?:\d+:\d+)\s*(?:am|pm)))?)"
        matches = re.findall(pattern, request_result)

        if matches:
            plans = []
            for match in matches:
                try:
                    # task = match[1]  # this neglected the time information, disposed
                    task = match[0]  # get the whole string, including the time info as the tast str
                    if match[2] == "from":
                        # from ... to ... structure
                        start_time = datetime.datetime.combine(date
                                                               , datetime.datetime.strptime(match[3].replace(" ", ""),
                                                                                            "%I:%M%p").time())
                        end_time = datetime.datetime.combine(date
                                                             , datetime.datetime.strptime(match[4].replace(" ", ""),
                                                                                          "%I:%M%p").time())
                    elif match[2] == 'at':
                        # at ... structure
                        start_time = end_time = datetime.datetime.combine(date
                                                                          , datetime.datetime.strptime(
                                match[3].replace(" ", ""), "%I:%M%p").time())
                    else:
                        raise Exception()
                    plans.append({
                        "task": task,
                        "start time": start_time,
                        "end time": end_time,
                    })
                except:
                    # logging.error("Bad Structure of GPT's response: Neither 'from...to...' or 'at...' structure")
                    logging.error(f"Response: {request_result}")
                    logging.error(e.__traceback__)
                    logging.error(e.__context__)

            logging.info(plans)
            return plans
        else:
            raise Exception(f"Regex parsing error after requesting plans. Request result: {request_result}")

    def plan_in_detail(agent, plan: dict, time_granularity: datetime.timedelta, date) -> list[dict]:
        """
        generate more detailed plan on the basis of a broad stroke plan(or just a relatively not detailed plan)
        :param agent:
        :param plan: a dict with keys of those mentioned in plan_in_broad_strokes
        :param time_granularity: the time granularity that the generated plan should be (e.g. 15 minutes) in NL
        :return: a more detailed list of plan

        """

        text_base = f"""
        Name:{agent.Name} (age: {agent.Age})
        Innate traits: {agent.Personality}
        {agent.Summarize}
        {agent.Name} plans to {plan['task']} date. {agent.Name} will do the following things in this time period
        [Example format: 
         4:00 pm: grab a light snack, such as a piece of fruit, a granola bar, or some nuts.
         4:05 pm: take a short walk around his workspace.]
         (Precise to {time_granularity.total_seconds() / 60} minutes):

        """

        request_result = request_GPT.request(text_base)

        # a sample
        # request_result = """
        # 9:00 am: Wake up, take a shower and get ready for the day.
        #  9:15 am: Eat a healthy breakfast such as oatmeal, eggs, or yogurt.
        #  9:30 am: Take a short walk to the university campus.
        #  9:45 am: Arrive at the university and prepare for classes.
        #  10:00 am: Attend classes and take notes.
        #  10:45 am: Take a break and review the notes taken in class.
        #  11:00 am: Get ready for the next class.
        # """

        pattern = r"((?:\d+:\d+)\s*(?:am|pm)).*:\s*(.+)"
        matches = re.findall(pattern, request_result)
        if matches:
            plans = []
            for i in range(len(matches)):
                match = matches[i]
                try:
                    # task = match[1]  # this neglected the time information, disposed
                    task = match[1]  # get the whole string, including the time info as the tast str
                    start_time = datetime.datetime.combine(date
                                                           , datetime.datetime.strptime(match[0].replace(" ", ""),
                                                                                        "%I:%M%p").time())
                    if i < len(matches) - 1:
                        end_time = datetime.datetime.combine(date
                                                             , datetime.datetime.strptime(
                                matches[i + 1][0].replace(" ", "")
                                , "%I:%M%p").time())
                    else:
                        end_time = plan['end time']
                    plans.append({
                        'task': task,
                        'start time': start_time,
                        'end time': end_time,
                    })
                except Exception as e:
                    logging.error(f"Response: {request_result}")
                    logging.error(e.__traceback__)
                    logging.error(e.__context__)
                    # raise Exception("Bad Structure of GPT's response(detailed): Neither 'from...to...' or 'at...' structure")

            logging.info(plans)
            return plans
        else:
            raise Exception(f"Regex parsing error after requesting plans. Request result: {request_result}")
    
    def reprioritize(agent: Agent, **kwargs):
        """ Reprioritize task list
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

