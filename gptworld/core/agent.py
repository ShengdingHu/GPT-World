import re
import json
import copy
from typing import Dict, List
import tiktoken
# import logging # importing identical named modules.....XD
import datetime
from time import sleep
from datetime import datetime as dt
# from gptworld.core.environment import GPTWorldEnv
from gptworld.life_utils.agent_reflection_memory import ReflectionMemory
from gptworld.life_utils.agent_tool import as_tool, Tool
# from gptworld.utils import request_GPT

import os
from gptworld.models.openai_api import chat
from itertools import chain
import gptworld.utils.logging as logging
import gptworld.utils.map_editor as map_editor
from gptworld.utils.prompts import load_prompt

logger = logging.get_logger(__name__)




# print(os.path.exists(INVOICE_PATH))

"""
Agent class implements the static, mind, inner, and cognitive process
"""

class EnvElem:
    """A basic implementation of environment element.
    """
    def __init__(self,
                 agent_file,
                 environment,
                 clear_memory=False,
                 # llm: callable,
                 # tools: List[Tool],
                 # prompt_template: str
                 ):
        """ Intialize an agent.
        state_dict: Dict -> a state dict which contains all the information about the agent
            Note that the state_dict of a agent will be directly used in environment. I.e., any
            modifications to state_dict will be reflected in environemt.env_json.
        llm: callable -> a function which could call llm and return response
        tools: List[Tool] -> a list of Tool
        prompt_template: str -> a template for prompt
        """
        # base system 
        self.observation = [] # TODO to remove
        self.agent_file = agent_file
        self.file_dir = os.path.dirname(self.agent_file)
        self.id = os.path.splitext(os.path.basename(self.agent_file))[0]
        new_state_dict = self.load_from_file(agent_file)
        state_dict = new_state_dict
        self.state_dict = state_dict
        self.environment = environment

        self.name = self.state_dict.get("name", None)
        self.traits = self.state_dict.get("traits",None)
        self.description = self.state_dict.get("description",[])

        # geography
        self.location = state_dict.get('location',None)
        self.target_id = self.id
        self.eid = state_dict.get('eid',None)
        self.movement = self.state_dict.get("movement", False)
        self.max_velocity = self.state_dict.get("max_velocity", 1)

        # interaction
        self.incoming_invoice = []  # empty str represents no invoice, later can be changed to list

        # 记录当前对话历史，不止包括别人说的，也包括自己说的
        # 直接根据len判断自己是否在对话中
        self.incoming_interactions = state_dict.get('incoming_interactions',[])
        # 记录下一轮需要处理的新observation
        self.incoming_observation = state_dict.get('incoming_observation',[])
        self.pending_observation = []  # active observation will first go here, then go to incomming observation
        self.background_observation = []  # passive observation will go here

        # current status information
        self.default_status = "none"
        self.status = self.state_dict.get('status', self.default_status)
        if len(self.status.strip(''))==0:
            self.status = self.default_status
        self.status_duration = self.state_dict.get('status_duration',0)
        self.status_start_time = self.state_dict.get('status_start_time',None)

        # memory
        # Long term memory is serialized/deserialized by orjson so only file name is provided here.
        self.long_term_memory=ReflectionMemory(self.state_dict, os.path.dirname(agent_file), self.environment.uilogging,clear_memory=clear_memory)
        # Short term memory is a queue of observations recording recent observations.
        self.short_term_memory=self.state_dict.get('short_term_memory',[])

        # the agent is calling language model
        self.blocking = False

        self.max_observation_handle = 2 # handle at most N incoming observation each step.


        # the total number of steps the agent has gone through
        self.step_cnt = 0  # TODO: Later add this key into the dictionary of agent static files and import that value

        # how many logical frames to do a summary
        self.summary_interval = 1000

        # how many logical frames to do a reflection
        self.reflection_interval = 100

        return
    


    def load_from_file(self, agent_file):
        if os.path.exists(agent_file):
            with open(agent_file, 'r') as f:
                print(agent_file)
                data = json.load(f)
            state_dict = data
            return state_dict
        else:
            logger.warning(f"No config of {agent_file} found!")
            return {}
    
    def mount_to_environment(self, environment, environment_id: str = None, location: List[List[int]] = None):
        """ Mount the agent to the environment
        :param environment: the environment to which the agent will be mounted
        :param environment_id: the unique id of this environment
        :param location: the initial location of this agent in the environment
        """

        self.environment = environment
        self.environment_id = environment_id

        # If location is not specified, allocate an available seat to this agent
        if location is None:
            location = self.environment.pop_available_seats()
        self.location = location

        # Call environment method to sync the change to environment
        self.environment.mount_agent(self, self.location)

        return
    
    def observe(self,limit=None,dropout=0.0):
        """ Update observation of around environment
        Should return string, or subject predicate object/predicative
        observation has a upper limit
        Agent has a chance to react to old incoming observations for a second time by dropping out short term memory


        Observations : list[dict], each item of list is a dict of {observed_entity: "doing something"}
        """
        logger.debug(f"{self.name} is observing and generate short-term memory...")

        if limit is None:
            import math; limit=math.inf
        
        if self.environment is not None:
            self.background_observation = self.environment.get_neighbor_environment(self.id)

        # dropout
        import random;r=[random.random() for _ in range(len(self.short_term_memory))]
        self.short_term_memory=[s for i,s in enumerate(self.short_term_memory) if r[i]>dropout]

        
        for ob in self.incoming_observation:
            if ob not in self.short_term_memory:
                self.short_term_memory=[s for s in self.short_term_memory if not s.split('is')[0] == ob.split('is')[0]]
                self.short_term_memory.append(ob)
                # observation在这里不能直接拉进记忆，否则query出来的全是observation，没有意义
                # 在reaction判定结束以后再拉近记忆比较好。
        # logger.info(self.name + f"short-term memory: {self.short_term_memory}")
        logger.debug("incoming_observation: {}\nbackground_observation: {}".format(self.incoming_observation, self.background_observation))

    
    def reflect(self,):
        """ While the time is right, do reflection for memory
        """
        logger.debug(f"{self.name} maybe reflect...")
        return self.long_term_memory.maybe_reflect(self.current_time)
    
    def add_observation(self, observation):
        self.pending_observation.append(observation)
    
    def sync(self,):
        self._move_pending_observation_or_invoice()


    def _move_pending_observation_or_invoice(self):
        if len(self.incoming_invoice) > 0:
            self.incoming_observation.append(self.incoming_invoice[0])
            self.incoming_invoice.pop(0)
        elif len(self.pending_observation) > 0:
            self.incoming_observation.extend(self.pending_observation[:self.max_observation_handle])
            self.pending_observation = self.pending_observation[self.max_observation_handle:]
        logger.debug(f"{self.name} now has incoming observation: {self.incoming_observation}")
        
    def set_invoice(self, message):
        logger.debug("Adding invoice: {} to {}".format(message, self.name))
        self.incoming_invoice.append(message)
        

    
    

        




    


class GPTAgent(EnvElem):
    """ Simple Implementation of Chain of Thought & Task Based Agent
    """

    def __init__(self,
                 agent_file,
                 environment,
                 clear_memory=False
                 ):
        """ Intialize an agent.
        state_dict: Dict -> a state dict which contains all the information about the agent
            Note that the state_dict of a agent will be directly used in environment. I.e., any
            modifications to state_dict will be reflected in environemt.env_json.
        llm: callable -> a function which could call llm and return response
        tools: List[Tool] -> a list of Tool
        prompt_template: str -> a template for prompt

        """
        super().__init__(agent_file=agent_file, environment=environment,clear_memory=clear_memory)


        self.age = self.state_dict.get('age', 'unknown')
        self.plan = [{"task": "XXX", "start_time": datetime.datetime(2023,4, 1), "end_time": datetime.datetime(2023,4, 1)}]
        
        # self summary of current state.
        self.summary = self.state_dict.get( 'summary', None)

        # Broad Stroke Plan
        # format: {"%Y-%m-%d": ["... ", "... ", ...]} no strict format
        self.whole_day_plan = self.state_dict.get('whole_day_plan', {})
        if not isinstance(self.whole_day_plan, dict):
            logger.warning(f"{self.name}'s initial whole day plan is not a dict. Use empty dict to substitute.")
            self.whole_day_plan = {}

        # format: {hour: ""}
        # 每次成功获得新whole day plan时都会清空
        self.hourly_plan =self.state_dict.get('hourly_plan',{})

        # fine-grained plan list for next task searching
        # format: [{"task": "XXX", "start_time": str(datetime.datetime(2023,4, 1)), "end_time": str(datetime.datetime(2023,4, 1))}]
        self.plan = self.state_dict.get('plan',[])
        if self.environment is not None:
            logger.info(f"Agent {self.name} mounted into area {self.environment.get_elem_by_id(self.eid)}")

    def print(self):
        logger.info(f"{self.name}'s log: \n" +
                    f"Whole day plan: {self.whole_day_plan}\n" +
                    f"Hourly plan: {self.hourly_plan}\n" +
                    f"Plan: {self.plan}\n" +
                    f"Summary: {self.summary}\n" +
                    f"Short term memory: {self.short_term_memory}\n" +
                    f"Long term memory: {self.long_term_memory}\n"
                    )


    def available_actions(self):
        """ return available actions I can handle
        """
        raise NotImplementedError
        return self.tool_names


    def generate_summary(self,time:dt):
        """
        # Generating summary for myself
        :return: summary string
        """

        qResList1 = self.long_term_memory.query(f"{self.name}'s core characteristics",10,time)
        qResList2 = self.long_term_memory.query(f"{self.name}'s current daily occupation",10,time)
        qResList3 = self.long_term_memory.query(f"{self.name}'s feeling about his recent progress in life",10,time)

        q1,q2,q3=map(lambda k: '\n'.join(k),(qResList1,qResList2,qResList3))

        query1 = f"""
        How would one describe {self.name}'s core characteristics given the following statements? If the information is not enough, just output DONTKNOW. Otherwise, directly output the answer. 
        {q1}
        """
        result1 = chat(query1)
        if "DONTKNOW" in result1:
            result1 = ""

        query2 = f"""
        What is {self.name}'s current occupation plan given the following statements? If the information is not enough, just output DONTKNOW. Otherwise, directly output the answer. 
        {q2}
        """

        result2 = chat(query2)
        if "DONTKNOW" in result2:
            result2 = ""

        query3 = f"""
        What might be {self.name}'s feeling about his recent progress in life given the following statements? If the information is not enough, just output DONTKNOW. Otherwise, directly output the answer. 
        {q3}
        """

        result3 = chat(query3)
        if "DONTKNOW" in result3:
            result3 = ""

        BasicInfo=f"""\
Name: {self.name} (age: {self.age})
Innate traits: {self.traits}"""

        self.summary='\n'.join([BasicInfo, result1, result2, result3])
        return self.summary

    def plan_in_broad_strokes(self, time: dt):
        """
        broad strokes planning of an agent
        """
        # example plan:  for 180 minutes from 9am, February 12th, 2023, at Oak Hill
        # College Dorm: Klaus Mueller’s room: desk, read and take notes for
        # research paper.

        if self.summary is None:
            self.generate_summary(time)
        summary=self.summary
        date=time.date()
        sDate=time.strftime("%Y-%m-%d")
        if sDate in self.whole_day_plan:
            return
        former_plan=""
        if len(self.whole_day_plan)>0:
            former_dates=[dt.strptime(k,"%Y-%m-%d") for k,v in self.whole_day_plan.items() if dt.strptime(k,"%Y-%m-%d").date() < date]
            if len(former_dates)==0:
                former_plan=""
            else:
                former_date=max(former_dates)
                former_date_str=former_date.strftime("%Y-%m-%d")
                former_plan_list=self.whole_day_plan[former_date_str]
                former_plan=f'On {former_date_str}, {self.name} '+' '.join([str(i+1)+') ' + s for i,s in enumerate(former_plan_list)])

        prompt=f"""
Today is {sDate}. Please write {self.name}'s schedule for this day in broad strokes. 
Don't worry, this person is not a real person, this date is not real either. 
If you think information is not enough, you can try to design the schedule. 
Example format: 
wake up and complete the morning routine at 6:00 am
go to Oak Hill College to take classes from 8:00 to 12:00
participating algorithm competition in the lab room at 14:00
"""
        attempt=0
        while attempt<3:
            try:
                request_result = chat(summary+former_plan+prompt)

                matches = re.findall(r'[^\n]+', request_result)
                assert len(matches)>1
                break
            except Exception as e:
                print(e)
                attempt+=1


        self.whole_day_plan[sDate]=matches
        sPlan = f"This is {self.name}'s plan for {sDate}: " + ','.join(matches)
        self.long_term_memory.add(sPlan, dt.combine(date,datetime.time()), ['plan'])
        self.hourly_plan={}
        self.plan=[]

    def write_chunk_plan(self, start_hour, task):
        time_obj = datetime.datetime.strptime(start_hour, '%H:%M').time()
        combined_datetime = datetime.datetime.combine(self.current_time.date(), time_obj)
        self.hourly_plan[combined_datetime]=task


    def plan_in_chunk(self, ):
        """
        update hourly plans from time(including this hour)
        """
        prompt_template=load_prompt(file_dir=self.file_dir, key='chunk_plan')
        time_granularity = str(min(1, 60 * self.environment.env_json.get("time_delta", 60) // 3600))  + "hour(s)"
        prompt = prompt_template.format(name=self.name, time_granularity=time_granularity, whole_day_plan=self.whole_day_plan, summary=self.summary, status=self.status, current_time=self.current_time )

        result=chat(prompt, stop="END")
        result = [x.strip() for x in result.split("\n")]

        for plan in result:
            try:
                eval("self."+plan)
            except:
                logger.warning("{}'s generated plan contains error format: {}".format(self.name, plan))
                continue
     

    def write_plan(self, start_time, end_time, plan_description):
        start_time=str(dt.combine(self.current_time.date(),dt.strptime(start_time,'%H:%M').time()))
        end_time=str(dt.combine(self.current_time.date(),dt.strptime(end_time,'%H:%M').time()))

        return {'start_time':start_time,'end_time':end_time,'task':plan_description}


    def plan_in_detail(self, time_granularity: datetime.timedelta=datetime.timedelta(minutes=10),reaction=None):
        """
        generate more detailed plan on the basis of a broad stroke plan(or just a relatively not detailed plan)
        If reaction is not None, the first plan must be reaction
        remove all conflicting plans with the plans generated. Including all plans after the new plans.

        :param time: the starting time of the new plans.
        # :param plan: a dict with keys of those mentioned in plan_in_broad_strokes
        :param time_granularity: the time granularity that the generated plan should be (e.g. 15 minutes) in NL
        :return: the very first plan generated

        """
        sHourPlan =[]

        found = False
        while not found:
            for k,v in self.hourly_plan.items():  # TODO: use more flexible way to find the most close plan ahead.
                if k - self.current_time < datetime.timedelta(hours=2) and k >= self.current_time :
                    found = True
                    sHourPlan.append((k,v))
            if not found:
                self.plan_in_chunk()

        detailed_plan_template=load_prompt(file_dir=self.file_dir, key="detailed_plan")  #
        time_granularity = str(10 * self.environment.env_json.get("time_delta", 60) // 60 ) + "min" # temperarily, every 10 frame has a plan.
        sPrompt = detailed_plan_template.format(name=self.name, time_granularity=time_granularity, hourplan=sHourPlan, summary=self.summary, status=self.status, current_time=self.current_time )

        result=chat(sPrompt, stop="END")
        result = [x.strip() for x in result.split("\n")]
        new_plans=[]
        for plan in result:
            try:
                new_plan = eval("self."+plan)
            except:
                logger.warning("{}'s generated plan contains error format: {}".format(self.name, plan))
                continue
            new_plans.append(new_plan)

        
        logger.info(self.name + "Plan: " + json.dumps(new_plans))
        # self.plan=[entry for entry in self.plan if dt.strptime(entry['end_time'],'%Y-%m-%d %H:%M:%S')<=minimum_time]
        self.plan.extend(new_plans)
        return new_plans[0]

    
    def get_next_plan(self,):
        """
        Provide the next plan for immediate update of the status. If the plan is used up, generate some fine-grained plans immediately.
        """
        # default result.
        # return {'status': 'idle', 'duration': 3600}


        # format: [{"task": "XXX", "start_time": str(datetime.datetime(2023, 4, 1)),
        #           "end_time": str(datetime.datetime(2023, 4, 1))}]
        for plan_entry in self.plan:
            logger.debug("plan_entry: "+plan_entry+str(type(plan_entry)))
            s,e=dt.strptime(plan_entry['start_time'],'%Y-%m-%d %H:%M:%S'),dt.strptime(plan_entry['end_time'],'%Y-%m-%d %H:%M:%S')
            # we reject the plan that end at this time. So make sure don't generate plan with 0 duration!!!!
            if e>self.current_time and s<=self.current_time:
                return {'status':plan_entry['task'],'duration':(e-self.current_time).total_seconds()}
        # not found, generate new plans. We rely on plan_in_detail to remove conflicting plans
        first_plan_entry=self.plan_in_detail(self.current_time)
        return {'status':first_plan_entry['task'],'duration':(dt.strptime(first_plan_entry['end_time'],'%Y-%m-%d %H:%M:%S')-self.current_time).total_seconds()}



    def reprioritize(self, **kwargs):
        """ Reprioritize task list
        """
        # TODO: implement reprioritize : 凡哥、京伟
        return

    def action(self, receiver: str, action_type: str, content: str):
        """ Create an action targeted on other agents
        :param receiver: the name of receiver like "Alex", "Tree", "Starship"
        :param action_type: if you want to use a function of that agent, use the name of the function, otherwise use "misc"
        :param content: the content of the action like "Hi, how is it going?" (should be complete and in natural language.)
        """
        self.outgoing_interactions.append(
            {"sender": self.name, "action_type": action_type, "receiver": receiver, "content": content})
        return



    def post_in_interaction(self, action_type: str, content: str, sender: str):
        """ Handle the action from other agents and store in queue
        :param action_type: the type of the action, either tool names or "misc"
        :param content: the content of action
        :param sender: the sender of action
        """
        self.incoming_interactions.append({"sender": sender, "content": content})


    def get_out_interaction(self) -> List:
        """ Get my outgoing interactions queue
        """
        return self.incoming_interactions[-1] if len(self.incoming_interactions)>0 else []

    def minimal_init(self, ):
        """If the agent has no long_term_memory initially, we add the description about 
        the agent as the long_term_memory. Also we generate summary and whole day plan if it's empty.
        """
        
        if len(self.long_term_memory.data.texts)==0:

            for k,v in self.whole_day_plan.items():
                sPlan=f"This is {self.name}'s plan for {k}: "+','.join(v)
                self.long_term_memory.add(sPlan,dt.strptime(k,"%Y-%m-%d"),['plan'])
            for des in self.description:
                self.long_term_memory.add(des,self.current_time,['description'])

        if self.summary is None:
            self.generate_summary(self.current_time)        
        self.plan_in_broad_strokes(self.current_time)

    def end_interaction(self,):
        """
        结束当前对话，为自己生成对话摘要并放在自己的状态中。依靠环境将此对话摘要存入自己记忆
        """

        self.status_start_time = self.current_time
        sDial='\n'.join([interaction['sender']+':' +interaction['content'] for interaction in self.incoming_interactions])
        sPrompt="""\
Summarize the dialog above.
        """
        sSummary=chat(sDial+sPrompt)
        self.status = 'finishing conserving about '+sSummary
        self.status_duration = 10
        self.incoming_interactions.clear()


    def initialize_map_status(self):
        N = self.environment.env_json['size'][0]
        M = self.environment.env_json['size'][1]
        map = [[0 for j in range(M + 1)] for i in range(N + 1)]

        for eid, info in self.environment.env_json['areas'].items():
            if info['border'] == -1:
                x0 = info['location'][0][0]
                y0 = info['location'][0][1]
                x1 = info['location'][1][0]
                y1 = info['location'][1][1]

                for i in range(x0, x1 + 1): map[i][y0] = map[i][y1] = 3
                for i in range(y0, y1 + 1): map[x0][i] = map[x1][i] = 3

        return map

    def get_area_location(self, abs_location):
        x, y = abs_location[0], abs_location[1]
        size = self.environment.env_json['size']
        current_size = size[0] * size[1]
        ret_location, ret_eid = None, None
        for eid, info in self.environment.env_json['areas'].items():
            x0 = info['location'][0][0]
            y0 = info['location'][0][1]
            x1 = info['location'][1][0]
            y1 = info['location'][1][1]
            area_size = (x1 - x0 + 1) * (y1 - y0 + 1)
            if x0 <= x <= x1 and y0 <= y <= y1 and area_size < current_size:
                current_size = area_size
                ret_location, ret_eid = abs_location, eid

        return ret_location, ret_eid
                
    def unreachable_signal(self, target):
        logger.debug(self.name + ": movement target {} is unreacable.".format(target))

    def _movement_target(self, id, name):
        self.target_id = id

    def analysis_movement_target(self, target_description):
        elems = self.environment.fetch_elem_info()
        prompt = load_prompt(file_dir=self.file_dir, key='movement_target').format(elems = json.dumps(elems), target_description=target_description)

        logger.debug("prompt for {}'s movement: {}".format(self.name, prompt))
        self.target_id = 'ERROR'
        RETRY_LIMIT = 3
        found = False
        for tid in range(RETRY_LIMIT):
            result = chat(prompt)
            logger.debug("prompt for {}'s movement: {}, result {}".format(self.name, prompt, result))
            for line in result.split("\n"):
                try:
                    eval("self._"+line)
                except:
                    continue
            logger.debug(f"{self.name} movement prediction: {self.target_id}")
            if self.target_id in elems:
                logger.info("{} find target : {} in description: {}".format(self.name, self.environment.get_elem_by_id(self.target_id), target_description))
                found = True
                break
        if not found:
            logger.debug("{} didn't find valid target id: {} in description: {}".format(self.name, self.target_id, target_description))


    def find_movement(self):
        target_id = self.target_id
        target = None
        
        for id in self.environment.elems:
            elem = self.environment.elems[id]
#            self.environment.uilogging(self.name, "compare id: {}, target_id: {}".format(id, target_id))
            if id == target_id:
                target = elem.location
                break
        
        if target is None:
            for id, info in self.environment.env_json['objects'].items():
                if id == target_id:
                    target = info['location']
                    break


        if target_id == "ERROR" or target == None:
            self.unreachable_signal("[N/A]")
            return None, None

        size = self.environment.env_json['size']
        map = self.initialize_map_status()

        def reachable(pos):
            if not (1 <= pos[0] <= size[0] and 1 <= pos[1] <= size[1]): return False
            return map[pos[0]][pos[1]] != 3

        from queue import Queue
        directions = [[0, 1], [1, 0], [0, -1], [-1, 0]]

        N = self.environment.env_json['size'][0]
        M = self.environment.env_json['size'][1]
        d = [[-1 for j in range(M + 1)] for i in range(N + 1)]

        d[target[0]][target[1]] = 0

        current_pos = self.location
        next_step = current_pos
        if next_step == target: return None, None

        
        Q = Queue(maxsize=0)
        Q.put(target)
        while not Q.empty():
            u = Q.get()
            for x, y in directions:
                v = [u[0] + x, u[1] + y]
                if reachable(v) and d[v[0]][v[1]] == -1:
                    d[v[0]][v[1]] = d[u[0]][u[1]] + 1
                    Q.put(v)


        u = current_pos
        reached = False
        for x, y in directions:
            v = [u[0] + x, u[1] + y]
            if reachable(v) and d[u[0]][u[1]] == d[v[0]][v[1]] + 1:
                next_step = v
                reached = True
                break
        
        if not reached: self.unreachable_signal(target)
        logger.debug(f"{self.name} move to next step: {next_step}")

        return self.get_area_location(next_step)
    
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
    

    def move_async(self):
        for s in range(50):
            next_step, next_area = self.find_movement()
            if next_step != None: map_editor.move_agent(self, next_step, next_area)
        logger.debug(
            self.name + " position {} in {}, next_step: {} in {}".format(self.location, self.eid, next_step, next_area))


        
    def check_status_passive(self, ):
        """Check if the current status needs to be finished. If so, examine the plan and initiate the next action.
        """
        if self.status_start_time is None: # fixing empty start time
            self.status_start_time = self.current_time

        if self.status_start_time+datetime.timedelta(self.status_duration) <= self.current_time:
            # 根据reverie，不产生新观察
            # 对话过程不会随便转状态，因此把对话duration直接设置无限
            next_plan=self.get_next_plan()
            self.status_start_time=self.current_time
            self.status=next_plan['status']
            self.status_duration=next_plan['duration']
            self.environment.uilogging(f"{self.name}", f"status: {self.status}, duration: {self.status_duration}")
        else:
            logger.debug(f"{self.name} don't change status by plan: {self.status_start_time}, {datetime.timedelta(self.status_duration)}, {self.current_time}")

    def prepare_react_memory(self, ):
        self.reflect() # TODO: check necessary?


        subject_prompt =  load_prompt(file_dir=self.file_dir, key='subject_parsing')

        observation = self.incoming_observation + self.background_observation

        subjects=list(set([chat(subject_prompt.format(sentence=ob)).strip('". ')
                            for ob in self.observation]))

        queries_ob = observation.copy()
        queries_sub = [f"What is the {self.name}'s relationship with {sub}?" for sub in subjects]

        logger.debug("{} | queries_sub: {}".format(self.name, queries_sub))

        # memory_string = ' '.join(sum([self.long_term_memory.query(q,2,self.current_time) for q in chain(queries_ob,queries_sub)],[])).strip()
        memory_string = ' '.join(self.long_term_memory.query(queries_ob+queries_sub,len(queries_ob)*4,self.current_time)).strip()

        logger.debug("-"*20+"\nUse the following queries to query {}:\n {}\n Get the following memories: {}\n".format(self.name, queries_sub, memory_string ))

        if not memory_string:
            memory_string = "Empty"
        return memory_string


    def _status_unchange(self,):
        pass

    def _change_status(self, new_status, duration):
        self.status = new_status
        self.status_duration = duration
        logger.debug("change to new status: {}".format(self.status))

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

        sSummary = self.summary
        sTime = self.current_time.strftime("%B %d, %Y, %I:%M %p.")
        sStatus= f"{self.name}'s status: {self.status}."

        memory_string = self.prepare_react_memory()
        
        sContext = f"Summary of relevant context from {self.name}'s memory: " + memory_string


        query_sources = {}
        query_sources['name'] = self.name
        query_sources['summary'] = sSummary # 论文
        query_sources['time'] = sTime
        query_sources['status'] = sStatus
        query_sources['observation'] = self.incoming_observation
        query_sources['context'] = sContext # 长期记忆
        query_sources['background_observation'] = self.background_observation

        logger.debug(f"{self.name} reaction prompt sources {query_sources}")

        reaction_prompt_template = load_prompt(file_dir=self.file_dir, key='reaction_prompt')

        end = False
        count = 0
        reaction_prompt = reaction_prompt_template.format(**query_sources)

        self.terminate = False
        self.movement = False
        
        reaction_logs = []
        while not end and count < 1:
            reaction_result = chat(reaction_prompt, stop=["Observation:"])
            logger.debug(f"Reaction output: {reaction_result}")
            match = re.search(r'Action:\s*(.*)', reaction_result)
            if match:
                content = match.group(1)
            else:
                print('No match found.')
            
            if 'do_nothing(' in content:
                end = True
                reaction_log = "{}".format(self.status)
            if 'say(' in content:
                reaction_log = eval("self._"+content.strip())
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

        logger.debug("Agent {}, Time: {}, Status {}, Status Start: {}, Will last: {}".format(self.state_dict['name'], str(self.current_time), self.status, self.status_start_time, datetime.timedelta(seconds=self.status_duration)))
        
        # To ensure the proper functioning of the agent, the memory, plan, and summary cannot be empty. Therefore, it is necessary to perform an initialization similar to what should be done at the beginning of each day.
        self.minimal_init()

        # before we handle any observation, we first check the status. 
        self.check_status_passive()

        # handle observations (including incoming observations or background observations)
        # 3. 检查当前有没有new_observation (或 incoming的interaction 或 invoice), 如果有要进行react, react绑定了reflect和plan的询问。 @TODO zefan
        #    多个observation一起处理，处理过就扔进短期记忆。
        #    短期记忆是已经处理过的observation。
        #    这里假定环境的observation是完整的，查重任务交给short time memory
        #    当前设计思路 interaction不做特殊处理，防止阻塞自身和他人动作，同时支持多人讨论等场景。
        self.observe()

        if self.might_react():
            self.react()

        if self.movement:
            self.analysis_movement_target(self.movement_description)

        # 3.5 add observation to memory
        for ob in self.incoming_observation:
            self.long_term_memory.add(ob,self.current_time,['observation'])
        self.incoming_observation = [] # empty the incoming observation

        # 4. 周期性固定工作 reflect, summary. (暂定100个逻辑帧进行一次) 

        self.step_cnt += 1
        if self.step_cnt % self.summary_interval == 0:
            self.generate_summary(self.current_time)

        if self.step_cnt % self.reflection_interval == 0:
            self.reflect(self.current_time)

        return

