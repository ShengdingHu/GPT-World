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
from gptworld.utils.logging import get_logger
import os
from gptworld.models.openai import chat
from gptworld.utils.envlog import envlog
from gptworld.core.agent import EnvElem

logger = get_logger(__file__)
logger.debug = print
logger.info = print



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
        self.status = state_dict.get('status', '')
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
        
        self.blocking = False
        logger.info(f"Objects {self.name} mounted into area {self.environment.get_area_name(self.eid)}")



    def step(self, current_time:dt):
        """ Call this method at each time frame
        """

        # 产生observation的条件： following reverie, 所有observation都是主体或客体的状态，所以这一步暂时直接交给环境处理。
        # 一类特殊状态，observation of interaction在对话结束给出摘要时才可以确定，此前不能被环境获取。reverie如何在对话开始时生成一个完整对话暂时没看明白
        # short time observation 应该屏蔽掉同主体同状态防止冗余

        logger.debug("Object {}, Current Time: {}".format(self.state_dict['name'], str(current_time)) )

        

        # TODO LIST， 每个人写一个if, 然后if里面用自己的成员函数写，避免大面积冲突。

        # 1. 如果当前正在向openai请求，调过这一步

        self.observe()

        might_react=len(self.incoming_interactions)>0 or len(self.observation)>0
        if might_react:
            self.reflect(current_time)

            sTime = current_time.strftime("It is %B %d, %Y, %I:%M %p.")
            sStatus= f"{self.name}'s status: {self.status}."
            sObservation = "Observation: " + '\n'.join(self.observation)
            queries=self.observation
            if len(self.incoming_interactions)>0:
                for i,interaction in reversed(self.incoming_interactions):
                    if i>=2:
                        break
                    queries.append(interaction['sender']+':' +interaction['content'])
            # 一点小修改：加上对话的最后几轮作为query

            sContext = f"Summary of relevant context from {self.name}'s memory: " + \
                    ' '.join(sum([self.long_term_memory.query(q,2,current_time) for q in queries],[]))



        if len(self.observation)>0:
            #
            sPrompt = f"""
1. Should {self.name} react to the observation? Say yes or no. 
If yes, tell me about the reaction, omitting the subjective. For example, say 'eating' instead of '{self.name} eats'.  
2. Does this reaction contents some content that need to be generated in a sentence or paragraph? Say yes or no.  
If yes, tell me the content being said in double quotes. 
3. Does this reaction has a specific target? Say yes or no. 
If yes, tell me the name or how would {self.name} call it. 
4. Also tell me if this reaction terminates {self.name}'s status, Say yes or no. 
5. Does this reaction involve {self.name} moving to a new location? Say yes or no. 
Strictly obeying the Output format:

```
1. <Yes/No for being a reaction> : <reaction>
2. <Yes/No for generation> : <content being generated>
3. <Yes/No for targeting> : <target name>
4. <Yes/No for terminating self status> 
5. <Yes/No for movement>
```
"""
            result=chat('\n'.join([sSummary,sTime,sStatus,sObservation,sContext,sPrompt]))
            
            lines=result.split('\n')
            if len(lines)<5:
                logging.warning('abnormal reaction:'+result)
            # line_split=[line.strip().split('$$') for line in lines]
            finds=[line.find('Yes') for line in lines]
            should_react,reaction=finds[0]>=0,lines[0][finds[0]+4:].strip().strip(':').strip()
            should_oral,oral=finds[1]>=0,lines[1][finds[1]+4:].strip().strip(':').strip()
            have_target,target=finds[2]>=0,lines[2][finds[2]+4:].strip().strip(':').strip()
            terminate=finds[3]>=0
            movement=finds[4]>=0


            # should_react, reaction=line_split[0][1], line_split[0][2].strip(':').strip()
            # should_oral,oral=line_split[1][1], line_split[1][2].strip(':').strip()
            # have_target,target=line_split[2][1], line_split[2][2].strip(':').strip()
            # terminate =line_split[3][1]

            if should_react:
                if should_oral:
                    reaction_content = reaction+' Also saying: '+oral
                else:
                    reaction_content=reaction
                if not have_target:
                    target=None

                envlog(self.name, reaction_content)
                if self.environment is not None:
                    self.environment.parse_action(self, target, reaction_content)
                if terminate:
                    self.status=reaction
                    self.status_duration=0
                    self.status_start_time=current_time
                    self.plan_in_detail(current_time)

        # TODO LIST， 每个人写一个if, 然后if里面用自己的成员函数写，避免大面积冲突。

        # 1. 如果当前正在向openai请求，调过这一步

        # 2. 检查自己当前动作是否需要结束，如果需要，则检查plan，开启下一个动作 （如果下一步没有 fine-grained sroke, 就plan）。 @TODO jingwei

        # 3. 检查当前有没有new_observation (或 incoming的interaction 或 invoice), 如果有要进行react, react绑定了reflect和plan的询问。 @TODO zefan
        #    多个observation一起处理，处理过就扔进短期记忆。
        #    短期记忆是已经处理过的observation。

        # 4. 周期性固定工作 reflect, summary. (暂定100个逻辑帧进行一次) @TODO jingwei

        # 5. 每个帧都要跑下寻路系统。 @TODO xingyu


        return


    