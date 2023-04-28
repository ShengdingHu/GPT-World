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

import gptworld.utils.logging as logging
import gptworld.utils.map_editor as map_editor
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
        self.agent_file = agent_file
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
        self.movement = self.state_dict.get("movement", "static")
        self.max_velocity = self.state_dict.get("max_velocity", 1)

        # interaction
        self.incoming_interactions = [{"sender": "A", "message": "XXX"}]
        self.incomming_objection = []
        self.incoming_invoice = []  # empty str represents no invoice, later can be changed to list

        # 记录当前对话历史，不止包括别人说的，也包括自己说的
        # 直接根据len判断自己是否在对话中
        self.incoming_interactions = state_dict.get('incoming_interactions',[])
        # 记录下一轮需要处理的新observation
        # self.observation进行过去重，incoming_observation没有去重
        self.incoming_observation = state_dict.get('incoming_observation',[])
        self.pending_observation = []

        # current status information
        self.status = self.state_dict.get('status','idle')
        self.status_duration = self.state_dict.get('status_duration',0)
        self.status_start_time = self.state_dict.get('status_start_time',None)

        # memory
        # Long term memory is serialized/deserialized by orjson so only file name is provided here.
        self.long_term_memory=ReflectionMemory(self.state_dict, os.path.dirname(agent_file), self.environment.uilogging,clear_memory=clear_memory)
        # Short term memory is a queue of observations recording recent observations.
        self.short_term_memory=self.state_dict.get('short_term_memory',[])

        # the agent is calling language model
        self.blocking = False


        # the total number of steps the agent has gone through
        self.step_cnt = 0  # TODO: Later add this key into the dictionary of agent static files and import that value

        # how many logical frames to do a summary
        self.summary_interval = 1000

        # how many logical frames to do a reflection
        self.reflection_interval = 100

        return
    
    def invoice(self, ):
        # 往incomming_invoice里 加一个invoice，并让agent能够最高优先级地响应这个输入
        pass


    def load_from_file(self, agent_file):
        if os.path.exists(agent_file):
            with open(agent_file, 'r') as f:
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
        """
        logger.debug(f"{self.name} is observing and generate short-term memory...")

        if limit is None:
            import math; limit=math.inf
        
        if self.environment is not None:
            self.incoming_observation.extend(self.environment.get_neighbor_environment(self.id))

        # dropout
        import random;r=[random.random() for _ in range(len(self.short_term_memory))]
        self.short_term_memory=[s for i,s in enumerate(self.short_term_memory) if r[i]>dropout]

        self.observation = []
        while len(self.incoming_observation)>0 and len(self.observation)<limit:
            ob=self.incoming_observation[0]
            self.incoming_observation.pop(0)
            if ob not in self.short_term_memory:
                self.observation.append(ob)
                self.short_term_memory=[s for s in self.short_term_memory if not s.split('is')[0] == ob.split('is')[0]]
                self.short_term_memory.append(ob)
                # observation在这里不能直接拉进记忆，否则query出来的全是observation，没有意义
                # 在reaction判定结束以后再拉近记忆比较好。
        self.environment.uilogging(self.name, f"short-term memory: {self.short_term_memory}")
        return self.observation
    
    def reflect(self,time:datetime):
        """ While the time is right, do reflection for memory
        """
        logger.debug(f"{self.name} maybe reflect...")
        return self.long_term_memory.maybe_reflect(time)
    
    def add_observation(self, observation):
        self.pending_observation.append(observation)

    def _move_pending_observation_or_invoice(self):
        
        if len(self.incoming_invoice) > 0:
            self.incoming_observation.append(self.incoming_invoice[0])
            self.incoming_invoice.pop(0)
            return 
        if len(self.pending_observation) > 0:
            self.incoming_observation.extend(self.pending_observation)
            self.pending_observation = []
        logger.debug(f"{self.name} now has incomming observation: {self.incoming_observation}")
        
    def set_invoice(self, message):
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
        # format: {"%B %d %Y": ["... ", "... ", ...]} no strict format
        self.whole_day_plan = self.state_dict.get('whole_day_plan',{})
        if not isinstance(self.whole_day_plan,dict):
            self.whole_day_plan={}

        # format: {hour: ""}
        # 每次成功获得新whole day plan时都会清空
        self.hourly_plan =self.state_dict.get('hourly_plan',{})

        # fine-grained plan list for next task searching
        # format: [{"task": "XXX", "start_time": str(datetime.datetime(2023,4, 1)), "end_time": str(datetime.datetime(2023,4, 1))}]
        self.plan = self.state_dict.get('plan',[])
        if self.environment is not None:
            logger.info(f"Agent {self.name} mounted into area {self.environment.get_area_name(self.eid)}")



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

        # retrieved_record = """
        # Chris is a undergraduate student in Tsinghua University, Love to play tennis and expand knowledge on
        # many different regions. Major in Electrical Engineering, but join in the Natural Language Processing Research Team
        # , very busy at his schoolwork.
        # """
        qResList1 = self.long_term_memory.query(f"{self.name}'s core characteristics",10,time)
        qResList2 = self.long_term_memory.query(f"{self.name}'s current daily occupation",10,time)
        qResList3 = self.long_term_memory.query(f"{self.name}'s feeling about his recent progress in life",10,time)

        q1,q2,q3=map(lambda k: '\n'.join(k),(qResList1,qResList2,qResList3))

        query1 = f"""
        How would one describe {self.name}'s core characteristics given the following statements?
        {q1}
        """
        result1 = chat(query1)

        query2 = f"""
        What is {self.name}'s current occupation plan given the following statements?
        {q2}
        """

        result2 = chat(query2)

        query3 = f"""
        What might be {self.name}'s feeling about his recent progress in life given the following statements?
        {q3}
        """

        result3 = chat(query3)

        BasicInfo=f"""\
Name: {self.name} (age: {self.age})
Innate traits: {self.traits}"""

        self.summary=BasicInfo+result1 + result2 + result3
        return self.summary

    def plan_in_broad_strokes(self, time: dt):
        """
        broad strokes planning of an agent
        由于决定当天broad stroke plan必须要前一天的plan，因此whole day plan数据格式必须是日期-计划的字典，日期entry格式
        模仿reverie，这一步输出无确定格式，因为展示得whole day plan也并不是每一项都带了规范时间，有的at有的from to还带可能先后关系也没太大参考价值。
        与其费事处理这个，不如hour long部分才要求转固定格式。
        :param time: str representing the current day
        """
        # example plan:  for 180 minutes from 9am, February 12th, 2023, at Oak Hill
        # College Dorm: Klaus Mueller’s room: desk, read and take notes for
        # research paper.

        if self.summary is None:
            self.generate_summary(time)
        summary=self.summary
        date=time.date()
        sDate=time.strftime("%B %d %Y")
        if sDate in self.whole_day_plan:
            return # 不再生成
        former_plan=""
        if len(self.whole_day_plan)>0:
            former_dates=[dt.strptime(k,"%B %d %Y") for k,v in self.whole_day_plan.items() if dt.strptime(k,"%B %d %Y").date() < date]
            if len(former_dates)==0:
                former_plan=""
            else:
                former_date=max(former_dates)
                former_date_str=former_date.strftime("%B %d %Y")
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
        # chat拒绝给一个真人定schedule，遇到类似拒绝回答情况可以强调这不是一个真人
        attempt=0
        while attempt<3:
            try:
                request_result = chat(summary+former_plan+prompt)

        # deal with the situation where Chat-GPT refuse to give a plan
        # bad_response_pattern = "As an AI language model"
        # warning_to_gpt = "\nJust use the information above to generate the plan."
        #
        # while re.search(pattern=bad_response_pattern, string=request_result):
        #     request_result = chat(summary+former_plan+prompt + warning_to_gpt)
        #     sleep(1)

                matches = re.findall(r'[^\n]+', request_result)
                assert len(matches)>1
                break
            except Exception as e:
                print(e)
                attempt+=1

        # logging.info(self.whole_day_plan)

        self.whole_day_plan[sDate]=matches
        # 提交到记忆
        sPlan = f"This is {self.name}'s plan for {sDate}: " + ','.join(matches)
        self.long_term_memory.add(sPlan, dt.combine(date,datetime.time()), ['plan'])
        # 单小时plan和细粒度plan在触发全天broad stroke plan后更新
        self.hourly_plan={}
        self.plan=[]



    def plan_in_chunk(self, time:dt):
        """
        update hourly plans from time(including this hour)
        """
        hour=time.hour
        summary=self.summary if self.summary is not None else self.generate_summary(time)
        sWhole=f"Here's {self.name}'s plan of the whole day: "+ '\n'.join([str(i+1)+') ' + s for i,s in enumerate(self.whole_day_plan[dt.strftime(time,"%B %d %Y")])])
        sPrompt=f"""
Please write {self.name}'s schedule of finer-grained actions for this day for each hour starting from {str(hour)}:00. 
Don't worry, this person is not a real person. 
every chunk of the schedule must be exactly 1 hour long. 
always use military time. 
Example format: 
10$$ wake up and complete the morning routine
11$$ go to Oak Hill College to take classes
12$$ participating algorithm competition in the lab room
13$$ have a walk at school
14$$ coding in chunks
"""
        result=chat(summary+sWhole+sPrompt)
        sEntries=re.findall(r"(\d+)\$\$([^\n]*)",result)
        for entry in sEntries:
            start_hour=int(entry[0].split(':')[0])
            task=entry[1].strip()
            self.hourly_plan[start_hour]=task


    def plan_in_detail(self, time:dt, time_granularity: datetime.timedelta=datetime.timedelta(minutes=10),reaction=None):
        """
        generate more detailed plan on the basis of a broad stroke plan(or just a relatively not detailed plan)
        If reaction is not None, the first plan must be reaction
        remove all conflicting plans with the plans generated. Including all plans after the new plans.

        :param time: the starting time of the new plans.
        # :param plan: a dict with keys of those mentioned in plan_in_broad_strokes
        :param time_granularity: the time granularity that the generated plan should be (e.g. 15 minutes) in NL
        :return: the very first plan generated

        """

        # find the corresponding hour plans.
        hour=time.hour
        if hour not in self.hourly_plan:
            self.plan_in_chunk(time)
        context=[]
        for k,v in self.hourly_plan.items():
            if k-hour<2 and k>=hour:
                context.append((k,v))

        summary=self.summary
        sHourPlan=f"Here's {self.name}'s plan of the incoming hours: " + '\n'.join([str(k)+':00 '+v for k,v in context])
        timestring=time.strftime('%H:%M')
        sReaction=f'The first plan must be "{reaction}". And the time for this plan must be sufficient. ' if reaction is not None else ""
        sPrompt=f"""
Please write {self.name}'s schedule of finer-grained precise to {time_granularity.total_seconds() / 60} minutes) \
of this period starting from {timestring}. 
Don't worry, this person is not a real person. 
always use military time.  
{sReaction}
Example format: 
11:00 - 12:15 $ Wake up, take a shower and get ready for the day.
12:15 - 12:30 $ Eat a healthy breakfast such as oatmeal, eggs, or yogurt.
12:30 - 12:45 $ Take a short walk to the university campus.
12:45 - 13:00 $ Arrive at the university and prepare for classes.
13:00 - 13:45 $ Attend classes and take notes.
13:45 - 14:00 $ Take a break and review the notes taken in class.
14:00 - 14:10 $ Get ready for the next class.
"""
        attempt=0
        while attempt<3:
            try:
                result=chat(summary+sHourPlan+sPrompt)

                sEntries=re.findall('(\d+:\d+)\s*-\s*(\d+:\d+)\s\$([^\n]*)',result)

                if not sEntries:
                    logger.error("Regex Parsing Error in plan_in_detail")
                    logger.error("Chat result = " + result)
                    raise Exception("Regex Error")
                break
            except Exception as e:
                print(e)
                attempt+=1

        new_plans=[]
        minimum_time=dt.combine(time.date(),dt.strptime(sEntries[0][0],'%H:%M').time())
        for entry in sEntries:
            start_time=str(dt.combine(time.date(),dt.strptime(entry[0],'%H:%M').time()))
            end_time=str(dt.combine(time.date(),dt.strptime(entry[1],'%H:%M').time()))
            task=entry[2].strip()
            new_plans.append({'start_time':start_time,'end_time':end_time,'task':task})
        
        self.environment.uilogging(self.name, "Plan: " + json.dumps(new_plans))
        self.plan=[entry for entry in self.plan if dt.strptime(entry['end_time'],'%Y-%m-%d %H:%M:%S')<=minimum_time]
        self.plan.extend(new_plans)
        return new_plans[0]

    
    def get_next_plan(self,current_time:dt):
        """
        给出下一个plan用于立刻更新状态。如果plan用完了，立刻生成一些fine-grained plan
        """
        # default result.
        # return {'status': 'idle', 'duration': 3600}


        # format: [{"task": "XXX", "start_time": str(datetime.datetime(2023, 4, 1)),
        #           "end_time": str(datetime.datetime(2023, 4, 1))}]
        for plan_entry in self.plan:
            s,e=dt.strptime(plan_entry['start_time'],'%Y-%m-%d %H:%M:%S'),dt.strptime(plan_entry['end_time'],'%Y-%m-%d %H:%M:%S')
            # we reject the plan that end at this time. So make sure don't generate plan with 0 duration!!!!
            if e>current_time and s<=current_time:
                return {'status':plan_entry['task'],'duration':(e-current_time).total_seconds()}
        # not found, generate new plans. We rely on plan_in_detail to remove conflicting plans
        first_plan_entry=self.plan_in_detail(current_time)
        return {'status':first_plan_entry['task'],'duration':(dt.strptime(first_plan_entry['end_time'],'%Y-%m-%d %H:%M:%S')-current_time).total_seconds()}



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

    def minimal_init(self,current_time: dt):
        """If the agent has no long_term_memory initially, we add the description about 
        the agent as the long_term_memory. Also we generate summary and whole day plan if it's empty.
        """
        
        if len(self.long_term_memory.data.texts)==0:

            # logging.info(self.whole_day_plan)

            for k,v in self.whole_day_plan.items():
                sPlan=f"This is {self.name}'s plan for {k}: "+','.join(v)
                self.long_term_memory.add(sPlan,dt.strptime(k,"%B %d %Y"),['plan'])
            for des in self.description:
                self.long_term_memory.add(des,current_time,['description'])

        if self.summary is None:
            self.generate_summary(current_time)
        self.plan_in_broad_strokes(current_time)

    def end_interaction(self,current_time:dt):
        """
        结束当前对话，为自己生成对话摘要并放在自己的状态中。依靠环境将此对话摘要存入自己记忆
        """

        self.status_start_time = current_time
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

        for id, info in self.environment.env_json['areas'].items():
            for i in range(info['location'][0][0], info['location'][1][0] + 1):
                for j in range(info['location'][0][1], info['location'][1][1] + 1):
                    map[i][j] = info['border']
        return map
                
    def unreachable_signal(self, target):
        self.observe()  # TODO: 为什么这里要 observe
        print('Target {} is unreacable.'.format(target))

    def analysis_movement_target(self, target_description):
        target_candidate = []
        for obj in self.environment.objects:
            target_candidate.append({'name':self.environment.objects[obj].name, 'id':self.environment.objects[obj].id})
        for agt in self.environment.agents:
            target_candidate.append({'name':self.environment.agents[agt].name, 'id':self.environment.agents[agt].id})
        prompt = f"""Now you want to perform a movement action. I will give you a list of 
        objects and agents that you might be your target. 
        List: {target_candidate}
        You target movement is : {target_description}
        Give me the id of the movement target (with out `id` prefix).
        """
        self.target_id = chat(prompt)

#        self.environment.uilogging(self.name, "target prompt: {}".format(target_description))

    def find_movement(self):
        logger.debug("walk to {}".format())
        def abs_location(pos, eid):
            area_delta = self.environment.env_json['areas'][eid]['location'][0]
            target = [pos[0] + area_delta[0] - 1, pos[1] + area_delta[1] - 1]
            return target

        target_id = self.target_id
        target = None
        for id, info in self.environment.env_json['objects'].items():
#            self.environment.uilogging(self.name, "compare id: {}, target_id: {}".format(id, target_id))
            if id == target_id:
                target = abs_location(info['location'], info['eid'])
                break

#        self.environment.uilogging(self.name, "target_id: {}".format(target_id))
#        self.environment.uilogging(self.name, "target_pos: {}".format(target))

        if target_id == "ERROR" or target == None:
            self.unreachable_signal("[N/A]")
            return

        size = self.environment.env_json['size']
        map = self.initialize_map_status()

        def reachable(pos):
            if not (1 <= pos[0] <= size[0] and 1 <= pos[1] <= size[1]): return False
            return map[pos[0]][pos[1]] != 3

        from queue import Queue
        directions = [[0, 1], [1, 0], [0, -1], [-1, 0]]

        INF = int(1e9)
        N = self.environment.env_json['size'][0]
        M = self.environment.env_json['size'][1]
        d = [[INF for j in range(M + 1)] for i in range(N + 1)]

        d[target[0]][target[1]] = 0

        Q = Queue(maxsize=0)
        Q.put(target)
        while not Q.empty():
            u = Q.get()
            for x, y in directions:
                v = [u[0] + x, u[1] + y]
                if reachable(v) and (v not in d):
                    d[v] = d[u] + 1
                    Q.put(v)


        next_step = u = abs_location(self.location, self.eid)
        if next_step == target: return next_step

        reached = False
        for x, y in directions:
            v = [u[0] + x, u[1] + y]
            if reachable(v) and v in d and d[u] == d[v] + 1:
                self.location = v
                reached = True
                break
        
        if not reached: self.unreachable_signal(target)
        return next_step

    def step(self, current_time:dt):
        """ Call this method at each time frame
        """

        # 产生observation的条件： following reverie, 所有observation都是主体或客体的状态，所以这一步暂时直接交给环境处理。
        # 一类特殊状态，observation of interaction在对话结束给出摘要时才可以确定，此前不能被环境获取。reverie如何在对话开始时生成一个完整对话暂时没看明白
        # short time observation 应该屏蔽掉同主体同状态防止冗余

        logger.info("Agent {}, Current Time: {}".format(self.state_dict['name'], str(current_time)) )
        
        # # 测试异步
        # if self.state_dict['name'].startswith("A"):
        #     time.sleep(20)
        # logger.debug("Agent {} is done".format(self.state_dict['name']))

        # 为了让agent正常工作，memory, plan, summary不能是空的。因此做一次类似于每日开始时应该进行的初始化
        self.minimal_init(current_time)

        # TODO LIST， 每个人写一个if, 然后if里面用自己的成员函数写，避免大面积冲突。



        # 0. If incoming_invoice is available, process it with the highest priority
    
        # 1. 如果当前正在向openai请求，调过这一步
        # if not self.incoming_invoice:  # Only move the pending observation without any incoming invoice
        self._move_pending_observation_or_invoice()
        # 2. 检查自己当前动作是否需要结束，如果需要，则检查plan，开启下一个动作 （如果下一步没有 fine-grained sroke, 就plan）。 @TODO jingwei
        if self.status_start_time is None: # fixing empty start time
            self.status_start_time = current_time
        if self.status_start_time+datetime.timedelta(self.status_duration) <= current_time:
            # 根据reverie，不产生新观察
            # 对话过程不会随便转状态，因此把对话duration直接设置无限
            next_plan=self.get_next_plan(current_time)
            self.status_start_time=current_time
            self.status=next_plan['status']
            self.status_duration=next_plan['duration']
            self.environment.uilogging(f"{self.name}", f"status: {self.status}, duration: {self.status_duration}")
        # 3. 检查当前有没有new_observation (或 incoming的interaction 或 invoice), 如果有要进行react, react绑定了reflect和plan的询问。 @TODO zefan
        #    多个observation一起处理，处理过就扔进短期记忆。
        #    短期记忆是已经处理过的observation。
        #    这里假定环境的observation是完整的，查重任务交给short time memory
        #    当前设计思路 interaction不做特殊处理，防止阻塞自身和他人动作，同时支持多人讨论等场景。
        self.observe()
        might_react=len(self.incoming_interactions)>0 or len(self.observation)>0
        if might_react:
            self.reflect(current_time)

            sSummary = self.summary
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

            memory_string = ' '.join(sum([self.long_term_memory.query(q,2,current_time) for q in queries],[])).strip()
            if len(memory_string) > 0:
                memory_string = "Empty"
            sContext = f"Summary of relevant context from {self.name}'s memory: " + memory_string

#         if len(self.incoming_interactions)>0:
#             # is currently in an conversation
#
#             # firstly, check whether the agent is becoming the target of interaction. If yes, change its status accordintly.
#             if (self.incoming_interactions)==1:
#                 self.status = 'conversing with '+self.incoming_interactions[0]['sender']
#                 self.status_start_time = current_time
#                 import math; self.status_duration=math.inf
#
#             # next, check if the other agent didn't response. If so, end the interaction.
#             if self.incoming_interactions[-1]['sender']==self.name:
#                 self.end_interaction(current_time)
#
#             else:
#                 sDialog ='Here is the dialogue history:'+'\n'.join([interaction['sender']+':' +interaction['content'] for interaction in self.incoming_interactions])
#                 sPrompt =f"""\
# Would {self.name} respond or stop the conversation? If yes, directly output the response. Example output:
# Yes. <response content>
# No.
#                 """
#                 result=chat(''.join([sSummary,sTime,sStatus,sObservation,sContext,sDialog,sPrompt]))
#                 if result.startwith('Yes'):
#                     content= '.'.join(result.split('.')[1:]).strip().split('\n')[0]
#                     new_interaction={'sender':self.name,'content':content}
#                     self.incoming_interactions.append(new_interaction)
#                 else:
#                     if not result.startwith('No'):
#                         logging.warning(logging.WARNING,'abnormal reaction response: '+result)
#                     self.end_interaction(current_time)

        if len(self.observation)>0:
            #
            sPrompt = f"""
1. Should {self.name} react to the observation? Say yes or no. 
If yes, tell me about the reaction, omitting the subjective. For example, say 'eating' instead of '{self.name} eats'.  
2. Is this reaction about saying something? Say yes or no.  
If yes, tell me the content being said in double quotes. 
3. Does this reaction has a specific target? Say yes or no. 
If yes, tell me the name or how would {self.name} call it. 
4. Also tell me if this reaction terminates {self.name}'s status, Say yes or no. 
5. Does this reaction involve {self.name} moving to a new location? Say yes or no. 
Strictly obeying the Output format, and don't omit answer to any of questions above

```
1. <Yes/No for being a reaction> : <reaction>
2. <Yes/No for saying something> : <content being said>
3. <Yes/No for targeting> : <target name>
4. <Yes/No for terminating self status> 
5. <Yes/No for movement>
```
"""
            try_num = 0
            send_message = '\n'.join([sSummary,sTime,sStatus,sObservation,sContext,sPrompt])
            logger.debug(f"Prompt of {self.name}'s reaction: "+send_message)
            while try_num < 3:
                result=chat(send_message)
                try:
                    lines=result.split('\n')
                    if len(lines)<5:
                        logger.warning('abnormal reaction:'+result)
                    # line_split=[line.strip().split('$$') for line in lines]
                    finds=[line.find('Yes') for line in lines]
                    should_react,reaction=finds[0]>=0,lines[0][finds[0]+4:].strip().strip(':').strip()
                    should_oral,oral=finds[1]>=0,lines[1][finds[1]+4:].strip().strip(':').strip()
                    have_target,target=finds[2]>=0,lines[2][finds[2]+4:].strip().strip(':').strip()
                    terminate=finds[3]>=0
#                    movement=finds[4]>=0
                    movement=1
                    break
                except IndexError:
                    logger.debug(f"Generated reaction {result}. Retrying...",)
                    try_num += 1
                    should_react = False
                    pass
            
                


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

                self.environment.uilogging(self.name, reaction_content)
                if self.environment is not None:
                    self.environment.parse_action(self, target, reaction_content)
                if terminate:
                    self.plan_in_detail(current_time,reaction=reaction)
                    next_plan=self.get_next_plan(current_time)
                    self.status_start_time = current_time
                    self.status = next_plan['status']
                    self.status_duration = next_plan['duration']
                    self.environment.uilogging(f"{self.name}",
                                               f"status: {self.status}, duration: {self.status_duration}")
                    # self.status=reaction
                    # self.status_duration=0
                    # self.status_start_time=current_time

                
            if movement:
                from IPython  import  embed; embed(header="True")
                self.analysis_movement_target(reaction)

        # 3.5 observation拉入记忆
        for ob in self.observation:
            self.long_term_memory.add(ob,current_time,['observation'])

        # 4. 周期性固定工作 reflect, summary. (暂定100个逻辑帧进行一次) 

        self.step_cnt += 1
        if self.step_cnt % self.summary_interval == 0:
            self.generate_summary(current_time)

        if self.step_cnt % self.reflection_interval == 0:
            self.reflect(current_time)


        # 5. 每个帧都要跑下寻路系统。 @TODO xingyu

        next_step = self.find_movement()
#        print(self.name, "MOVING!!! position {}, next_step: {}".format(self.location, next_step))

#        self.location = map_editor.move_agent(self, next_step)

        return

