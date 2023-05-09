import re
from typing import Dict, List
import logging
import datetime
from datetime import datetime as dt


from gptworld.models.openai_api import chat
from gptworld.core.element import EnvElem
from gptworld.utils.prompts import load_prompt
import gptworld.utils.logging as logging
logger = logging.get_logger(__name__)



class GPTEnvObject:
    """
    Object class implements the inactive objects, which has the ability to 
    1. produce routine action, such as growing, broadcasting a long-message. 
    2. react to the outside observation within the objects's ability.
    """


    def __init__(self,
                 state_dict,
                 environment,
                 ):
        """ Intialize an agent.
        state_dict: Dict -> a state dict which contains all the information about the agent
        llm: callable -> a function which could call llm and return response
        tools: List[Tool] -> a list of Tool
        prompt_template: str -> a template for prompt

        """
        self.id = state_dict['id']
        self.state_dict = state_dict
        self.name = state_dict['name']
        self.location = state_dict['location']
        self.size = state_dict.get('size', '')
        self.status = state_dict.get('status', 'here')
        self.eid = state_dict.get('eid', 'e_001')
        self.environment = environment


class GPTObject(EnvElem):
    """
    Object class implements the inactive objects, which has the ability to 
    1. produce routine action, such as growing, broadcasting a long-message. 
    2. react to the outside observation within the objects's ability.
    """


    def __init__(self,
                 agent_file,
                 environment,
                 ):
        """ Intialize an object.
        """
        super().__init__(agent_file=agent_file, environment=environment)

        self.description = self.state_dict.get("description", "")
        self.description = "\n".join(self.description)
        if len(self.description) == 0:
            summary_prompt_template = load_prompt(file_dir=self.file_dir, key='object_summary')
            summary_prompt = summary_prompt_template.format(name=self.name)

            self.description = chat(summary_prompt)
            logger.debug(f"Objects {self.name} is created with the following description: {self.description}")

        self.summary=f'Now you are act as a {self.name} in the virtual world, obeying following rules:\n' + self.description
        logger.info(f"Objects {self.name} mounted into area {self.environment.get_elem_by_id(self.eid)}")
        self.blocking = False

    def move_async(self, ):
        # Not implemented yet.
        pass


    def _act(self, description=None, target=None):
        if description is None:
            return ""
        if target is None:
            reaction_content = f"{self.name} performs action: '{description}'."
        else:
            reaction_content = f"{self.name} performs action to {target}: '{description}'."
        self.environment.broadcast_observations(self, target, reaction_content)
        return reaction_content
        

    def _say(self, description, target=None):
        if description is None:
            return ""
        if target is None:
            reaction_content = f"{self.name} says: '{description}'."
        else:
            reaction_content = f"{self.name} says to {target}: '{description}'."
        self.environment.broadcast_observations(self, target, reaction_content)
        return reaction_content


    def _move(self, description):
        if description is None:
            self.movement=False
        else:
            self.movement=True
            self.movement_description = description
        return description
    
    
    def might_react(self):
        return len(self.incoming_observation)>0 or len(self.background_observation)>0

    def react(self):
        """
        react.
        检查当前有没有new_observation (或 incoming的interaction 或 invoice), 如果有要进行react, react绑定了reflect和plan的询问。
        多个observation一起处理，处理过就扔进短期记忆。
        短期记忆是已经处理过的observation。
        这里假定环境的observation是完整的，查重任务交给short time memory
        当前设计思路 interaction不做特殊处理，防止阻塞自身和他人动作，同时支持多人讨论等场景。
        """

        # sSummary = self.summary
        sTime = self.current_time.strftime("%B %d, %Y, %I:%M %p.")
        sStatus= f"{self.name}'s status: {self.status}."

        # memory_string = self.prepare_react_memory()
        
        # sContext = f"Summary of relevant context from {self.name}'s memory: " + memory_string


        query_sources = {}
        query_sources['name'] = self.name
        # query_sources['summary'] = sSummary # 论文
        query_sources['time'] = sTime
        query_sources['status'] = sStatus
        query_sources['observation'] = self.incoming_observation
        # query_sources['context'] = sContext # 长期记忆
        query_sources['background_observation'] = self.background_observation

        logger.debug(f"{self.name} reaction prompt sources {query_sources}")

        reaction_prompt_template = load_prompt(file_dir=self.file_dir, key='reaction_prompt_object')

        end = False
        count = 0
        reaction_prompt = reaction_prompt_template.format(**query_sources)

        self.terminate = False
        self.movement = False
        
        reaction_logs = []
        while not end and count < 1:
            reaction_result = chat(reaction_prompt, stop=["Observation:"])
            logger.debug(f"{self.name}: Reaction output: {reaction_result}")
            match = re.search(r'Action:\s*(.*)', reaction_result)
            if match:
                content = match.group(1)
            else:
                print('No match found.')
            
            if 'do_nothing(' in content:
                end = True
                reaction_log = "{}".format(self.status)
            # if 'say(' in content:
            #     reaction_log = eval("self._"+content.strip())
            elif 'act(' in content:
                reaction_log = eval("self._"+content.strip())
            elif 'move(' in content:
                reaction_log = eval("self._"+content.strip())
            elif 'end(' in content:
                end = True
            count += 1
            reaction_logs.append(reaction_log)
            reaction_prompt += reaction_result + "\nObservation: [Observation omitted]\n"

        reaction_logs = " & ".join(reaction_logs)
        if len(reaction_logs) > 0:
            self.environment.uilogging(self.name, reaction_logs)
            logger.info(f"{self.name} react: {reaction_logs}")
            self.status = reaction_logs

        # # change status active # TODO: currently not in use!
        # change_status_prompt_template = load_prompt(file_dir=self.file_dir, key='change_status')
        # change_status_prompt = change_status_prompt_template.format(**query_sources, reaction=reaction_result)
        # result = chat(change_status_prompt)
        # for line in result.split("\n"):
        #     eval("self._"+line)


        # TODO: check if the old plan is invalid, if it is, generate new plan.
        if self.terminate:
            self.plan_in_detail(self.current_time, reaction = reaction_logs)
            next_plan=self.get_next_plan(self.current_time)
            self.status_start_time = self.current_time
            self.status = next_plan['status']
            self.status_duration = next_plan['duration']
            self.environment.uilogging(f"{self.name}",
                                        f"status: {self.status}, duration: {self.status_duration}")
            self.status=reaction_logs
            self.status_duration=0
            self.status_start_time=self.current_time

   


    def step(self, current_time:dt):
        """ Call this method at each time frame
        """
        self.current_time = current_time

        logger.debug("Object {}, Time: {}, Status {}, Status Start: {}, Will last: {}".format(self.state_dict['name'], str(self.current_time), self.status, self.status_start_time, datetime.timedelta(seconds=self.status_duration)))
        
        self.observe()

        if self.might_react():
            self.react()

        # if self.movement:
        #     self.analysis_movement_target(self.movement_description)

        # 3.5 add observation to memory
        for ob in self.incoming_observation:
            self.long_term_memory.add(ob,self.current_time,['observation'])
        self.incoming_observation = [] # empty the incoming observation

        # self.step_cnt += 1
        # if self.step_cnt % self.summary_interval == 0:
        #     self.generate_summary(self.current_time)

        # if self.step_cnt % self.reflection_interval == 0:
        #     self.reflect(self.current_time)
        return
