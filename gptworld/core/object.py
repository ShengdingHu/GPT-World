import re
import json
import copy
from typing import Dict, List
import tiktoken
import logging
import datetime
from datetime import datetime as dt
# from gptworld.core.environment import GPTWorldEnv
from gptworld.life_utils.agent_reflection_memory import ReflectionMemory
from gptworld.life_utils.agent_tool import as_tool, Tool
# from gptworld.utils import request_GPT
import os
from gptworld.models.openai_api import chat
from gptworld.core.agent import EnvElem
from gptworld.utils.prompts import load_prompt
import gptworld.utils.logging as logging
logger = logging.get_logger(__name__)



# # The color for intermediate result
# RESET = "\033[0m"  # reset color output
# GREEN = "\033[92m"  # Green text
# MAGENTA = "\033[35m"  # Magenta text
# RED = "\033[31m"  # Red text
# BOLD = "\033[1m"  # Bold text
# BLUE = "\033[34m"  # Blue text
#
# MAX_SHORT_TERM_MEMORY = 1500
# MAX_LONG_TERM_MEMORY = 1500
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
        """ Intialize an agent.
        state_dict: Dict -> a state dict which contains all the information about the agent
        llm: callable -> a function which could call llm and return response
        tools: List[Tool] -> a list of Tool
        prompt_template: str -> a template for prompt

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
        目前尽量塞主step函数简化变量调用，TODO:后期切成几个子函数方便维护
        """
        self.current_time = current_time

        logger.debug("Object {}, Time: {}, Status {}, Status Start: {}, Will last: {}".format(self.state_dict['name'], str(self.current_time), self.status, self.status_start_time, datetime.timedelta(seconds=self.status_duration)))
        
        # To ensure the proper functioning of the agent, the memory, plan, and summary cannot be empty. Therefore, it is necessary to perform an initialization similar to what should be done at the beginning of each day.
        # self.minimal_init()

        # before we handle any observation, we first check the status. 
        # self.check_status_passive()

        # handle observations (including incoming observations or background observations)
        # 3. 检查当前有没有new_observation (或 incoming的interaction 或 invoice), 如果有要进行react, react绑定了reflect和plan的询问。 @TODO zefan
        #    多个observation一起处理，处理过就扔进短期记忆。
        #    短期记忆是已经处理过的observation。
        #    这里假定环境的observation是完整的，查重任务交给short time memory
        #    当前设计思路 interaction不做特殊处理，防止阻塞自身和他人动作，同时支持多人讨论等场景。
        self.observe()

        if self.might_react():
            self.react()

        # if self.movement:
        #     self.analysis_movement_target(self.movement_description)

        # 3.5 add observation to memory
        for ob in self.incoming_observation:
            self.long_term_memory.add(ob,self.current_time,['observation'])
        self.incoming_observation = [] # empty the incoming observation

        # 4. 周期性固定工作 reflect, summary. (暂定100个逻辑帧进行一次) 

        # self.step_cnt += 1
        # if self.step_cnt % self.summary_interval == 0:
        #     self.generate_summary(self.current_time)

        # if self.step_cnt % self.reflection_interval == 0:
        #     self.reflect(self.current_time)

        return




#     def step(self, current_time:dt):
#         """ Call this method at each time frame
#         """

#         # 产生observation的条件： following reverie, 所有observation都是主体或客体的状态，所以这一步暂时直接交给环境处理。
#         # 一类特殊状态，observation of interaction在对话结束给出摘要时才可以确定，此前不能被环境获取。reverie如何在对话开始时生成一个完整对话暂时没看明白
#         # short time observation 应该屏蔽掉同主体同状态防止冗余

#         logger.debug("Object {}, Current Time: {}".format(self.state_dict['name'], str(current_time)) )

#         self._move_pending_observation_or_invoice()
#         if self.status_start_time is None: # fixing empty start time
#             self.status_start_time = current_time

#         # TODO LIST， 每个人写一个if, 然后if里面用自己的成员函数写，避免大面积冲突。

#         # 1. 如果当前正在向openai请求，调过这一步

#         self.observe()

#         might_react=len(self.incoming_interactions)>0 or len(self.observation)>0
#         if might_react:
#             self.reflect(current_time)

#             sTime = current_time.strftime("It is %B %d, %Y, %I:%M %p.")
#             sStatus= f"{self.name}'s status: {self.status} for {(current_time-self.status_start_time).total_seconds()} seconds."
#             sObservation = "Observation: " + '\n'.join(self.observation)
#             # queries=self.observation
#             # 一点小修改：加上对话的最后几轮作为query

#             # sContext = f"Summary of relevant context from {self.name}'s memory: " + \
#             #         ' '.join(sum([self.long_term_memory.query(q,2,current_time) for q in queries],[]))



#         if len(self.observation)>0:
#             #
#             sPrompt = f"""
# 1. Should {self.name} react to the observation? Say yes or no. 
# If yes, tell me about the reaction, omitting the subjective. For example, say 'eating' instead of '{self.name} eats'.  
# 2. Does this reaction contents some content that need to be generated in a sentence or paragraph? Say yes or no. This is a fake question, just say no.  
# If yes, tell me the content being said in double quotes. 
# 3. Does this reaction has a specific target? Say yes or no. 
# If yes, tell me the name or how would {self.name} call it. 
# 4. Also tell me if this reaction terminates {self.name}'s status, Say yes or no. 
# 5. Does this reaction involve {self.name} moving to a new location? Say yes or no. 
# Strictly obeying the Output format:

# ```
# 1. <Yes/No for being a reaction> : <reaction>
# 2. <Yes/No for generation> : <content being generated>
# 3. <Yes/No for targeting> : <target name>
# 4. <Yes/No for terminating self status> 
# 5. <Yes/No for movement>
# ```
# """

#             # send_message = '\n'.join([sTime,sStatus,sObservation,sContext,sPrompt])
#             send_message = '\n'.join([self.summary, sTime,sStatus,sObservation,sPrompt])
#             try_num = 0
#             while try_num < 3:
#                 result=chat(send_message)
#                 try:
#                     lines=result.split('\n')
#                     if len(lines)<5:
#                         logger.warning('abnormal reaction:'+result)
#                     # line_split=[line.strip().split('$$') for line in lines]
#                     finds=[line.find('Yes') for line in lines]
#                     should_react,reaction=finds[0]>=0,lines[0][finds[0]+4:].strip().strip(':').strip()
#                     should_oral,oral=finds[1]>=0,lines[1][finds[1]+4:].strip().strip(':').strip()
#                     have_target,target=finds[2]>=0,lines[2][finds[2]+4:].strip().strip(':').strip()
#                     terminate=finds[3]>=0
#                     movement=finds[4]>=0
#                     break
#                 except IndexError:
#                     logger.debug(f"Generated reaction {result}. Retrying...")
#                     try_num+=1
#                     pass

#             logger.debug(f"Prompt of {self.name}'s reaction: "+send_message+"Return message is "+result)



#             # should_react, reaction=line_split[0][1], line_split[0][2].strip(':').strip()
#             # should_oral,oral=line_split[1][1], line_split[1][2].strip(':').strip()
#             # have_target,target=line_split[2][1], line_split[2][2].strip(':').strip()
#             # terminate =line_split[3][1]

#             if should_react:
#                 if should_oral:
#                     reaction_content = reaction+' Also saying: '+oral
#                 else:
#                     reaction_content=reaction
#                 if not have_target:
#                     target=None

                
#                 if self.environment is not None:
#                     self.environment.uilogging(self.name, reaction_content)
#                     self.environment.broadcast_observations(self, target, reaction_content)
#                 if terminate:
#                     # object没有判定状态终止的机制，在这里duration随便填，记个开始时间就行。
#                     self.status=reaction
#                     self.status_duration=0
#                     self.status_start_time=current_time

#                     # self.plan_in_detail(current_time)

#         # TODO LIST， 每个人写一个if, 然后if里面用自己的成员函数写，避免大面积冲突。

#         # 1. 如果当前正在向openai请求，调过这一步

#         # 2. 检查自己当前动作是否需要结束，如果需要，则检查plan，开启下一个动作 （如果下一步没有 fine-grained sroke, 就plan）。 @TODO jingwei

#         # 3. 检查当前有没有new_observation (或 incoming的interaction 或 invoice), 如果有要进行react, react绑定了reflect和plan的询问。 @TODO zefan
#         #    多个observation一起处理，处理过就扔进短期记忆。
#         #    短期记忆是已经处理过的observation。

#         # 4. 周期性固定工作 reflect, summary. (暂定100个逻辑帧进行一次) @TODO jingwei

#         # 5. 每个帧都要跑下寻路系统。 @TODO xingyu


#         return



    