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
import bisect


logger = get_logger(__file__)
logger.debug = print
logger.info = print

"""
Agent class implements the static, mind, inner, and cognitive process
"""

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


class GPTAgent:
    """ Simple Implementation of Chain of Thought & Task Based Agent
    """

    def __init__(self,
                 state_dict: dict,
                 agent_file,
                 environment,
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
        self.agent_file = agent_file
        self.id = os.path.splitext(os.path.basename(self.agent_file))[0]
        new_state_dict = self.load_from_file(agent_file)
        state_dict.update(new_state_dict)
        self.state_dict = state_dict
        self.environment = environment

        self.incoming_interactions = [{"sender": "A", "message": "XXX"}]

        self.incomming_objection = ["XXXX",]

        self.incomming_invoice = []


        self.summary = "XXXX"

        self.plan = [{"task": "XXX", "start_time": datetime.datetime(2023,4, 1), "end_time": datetime.datetime(2023,4, 1)}]

        # 记录当前对话历史，不止包括别人说的，也包括自己说的
        # 直接根据len判断自己是否在对话中
        self.incoming_interactions = state_dict.get('incoming_interactions',[])

        # 记录下一轮需要处理的新observation
        # self.observation进行过去重，incoming_observation没有去重
        self.incoming_observation = state_dict.get('incoming_observation',[])

        self.pending_observation = []

        # Parse initial location from state dict. {"eid": "e_004", "location": [1,1]}
        self.location = state_dict.get('location',None)
        self.eid = state_dict.get('eid',None)

        # self summary of current state.
        self.summary = state_dict.get( 'summary', None)

        # Broad Stroke Plan
        # format: {"%B %d %Y": ["... ", "... ", ...]} no strict format
        self.whole_day_plan = state_dict.get('whole_day_plan',{})
        if not isinstance(self.whole_day_plan,dict):
            self.whole_day_plan={}

        # format: {hour: ""}
        # 每次成功获得新whole day plan时都会清空
        self.hourly_plan=state_dict.get('hourly_plan',{})

        # fine-grained plan list for next task searching
        # format: [{"task": "XXX", "start_time": str(datetime.datetime(2023,4, 1)), "end_time": str(datetime.datetime(2023,4, 1))}]
        self.plan = state_dict.get('plan',[])

        # current status information
        self.status=state_dict.get('status','')
        self.status_duration=state_dict.get('status_duration',0)
        self.status_start_time=state_dict.get('status_start_time',None)

        # Long term memory is serialized/deserialized by orjson so only file name is provided here.
        self.long_term_memory=ReflectionMemory(state_dict, os.path.dirname(agent_file))

        # Short term memory is a queue of observations recording recent observations.
        self.short_term_memory=state_dict.get('short_term_memory',[])

        # basic fingerprint
        self.name = state_dict.get("name", None)

        self.age= state_dict.get("age",None)

        self.traits= state_dict.get("traits",None)

        self.description=state_dict.get("description",[])

        # location movements
        self.movement = state_dict.get("movement", "static")

        self.max_velocity = state_dict.get("max_velocity", 1)

        # Type of the agent, either 'objective' or 'subjective'
        self.type = state_dict.get("type", None)

        self.status = state_dict.get('status', '')


        # The thinking kernel
        # self.llm = llm

        # The chain of thought prompt
        # self.prompt_template = prompt_template # template of promot, defined by user 

        # A List of Tool
        # self.tools = tools

        # Mapping from action name to action Tool object
        # self.tool_map = {}
        # self.tool_names = []
        # for tool in self.tools:
        #     self.tool_names.append(tool.tool_name)
        #     self.tool_map[tool.tool_name] = tool

        # self.tool_names_and_descriptions = "\n".join(
        #     [tool.tool_name + " - " + tool.tool_description for tool in self.tools])  # tool names and desctiptions

        # Whether the agent is moving ("moving" or "static")

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

        # the agent is calling language model
        self.blocking = False

        return
    
    def invoice(self, ):
        # 往 incomming invoice 里
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

    def available_actions(self):
        """ return available actions I can handle
        """
        return self.tool_names

    def observe(self,limit=None):
        """ Update observation of around environment
        Should return string, or subject predicate object/predicative
        observation has a upper limit,
        """
        logger.debug(f"{self.name} is observing ...")

        if limit is None:
            import math; limit=math.inf
        
        if self.environment is not None:
            self.incoming_observation.extend(self.environment.get_neighbor_environment(self.id))

        self.observation = []
        while len(self.incoming_observation)>0 and len(self.observation)<limit:
            ob=self.incoming_observation[0]
            self.incoming_observation.pop(0)
            if ob not in self.short_term_memory:
                self.observation.append(ob)
                self.short_term_memory=[s for s in self.short_term_memory if not s.split('is')[0] == ob.split('is')[0]]
                self.short_term_memory.append(ob)
        return self.observation

    def reflect(self,time:datetime):
        """ While the time is right, do reflection for memory
        """
        logger.debug(f"{self.name} maybe reflect...")
        return self.long_term_memory.maybe_reflect(time)

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
Example format: 
wake up and complete the morning routine at 6:00 am
go to Oak Hill College to take classes from 8:00 to 12:00
participating algorithm competition in the lab room at 14:00
"""
        # chat拒绝给一个真人定schedule，遇到类似拒绝回答情况可以强调这不是一个真人
        request_result = chat(summary+former_plan+prompt)
        matches=re.findall(r'[^\n]+',request_result)
        self.whole_day_plan[sDate]=matches
        # 提交到记忆
        sPlan = f"This is {self.name}'s plan for {sDate}: " + ','.join(matches)
        self.long_term_memory.add(sPlan, dt.combine(date,datetime.time()), ['plan'])
        # 单小时plan和细粒度plan在触发全天broad stroke plan后更新
        self.hourly_plan={}
        self.plan=[]


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

        # logging.info(f"Request GPT result(Broad strokes):\n{request_result}")

        # pattern = r"(?:\d+\))((.+) (from|at) ((?:\d+:\d+)\s*(?:am|pm))(?: to ((?:\d+:\d+)\s*(?:am|pm)))?)"
        # matches = re.findall(pattern, request_result)
        #
        # if matches:
        #     plans = []
        #     for match in matches:
        #         try:
        #             # task = match[1]  # this neglected the time information, disposed
        #             task = match[0]  # get the whole string, including the time info as the tast str
        #             if match[2] == "from":
        #                 # from ... to ... structure
        #                 start_time = datetime.datetime.combine(date
        #                                                        , datetime.datetime.strptime(match[3].replace(" ", ""),
        #                                                                                     "%I:%M%p").time())
        #                 end_time = datetime.datetime.combine(date
        #                                                      , datetime.datetime.strptime(match[4].replace(" ", ""),
        #                                                                                   "%I:%M%p").time())
        #             elif match[2] == 'at':
        #                 # at ... structure
        #                 start_time = end_time = datetime.datetime.combine(date
        #                                                                   , datetime.datetime.strptime(
        #                         match[3].replace(" ", ""), "%I:%M%p").time())
        #             else:
        #                 raise Exception()
        #             plans.append({
        #                 "task": task,
        #                 "start time": start_time,
        #                 "end time": end_time,
        #             })
        #         except:
        #             # logging.error("Bad Structure of GPT's response: Neither 'from...to...' or 'at...' structure")
        #             logging.error(f"Response: {request_result}")
        #             logging.error(e.__traceback__)
        #             logging.error(e.__context__)
        #
        #     logging.info(plans)
        #     return plans
        # else:
        #     raise Exception(f"Regex parsing error after requesting plans. Request result: {request_result}")

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
use 24 hour format rather than 12. 
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


    def plan_in_detail(self, time:dt, time_granularity: datetime.timedelta=datetime.timedelta(minutes=10)):
        """
        generate more detailed plan on the basis of a broad stroke plan(or just a relatively not detailed plan)
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
        sPrompt=f"""
Please write {self.name}'s schedule of finer-grained precise to {time_granularity.total_seconds() / 60} minutes) \
of this period starting from {timestring}. 
Don't worry, this person is not a real person. 
use 24 hour format rather than 12. 
Example format: 
11:00 - 12:15 $ Wake up, take a shower and get ready for the day.
12:15 - 12:30 $ Eat a healthy breakfast such as oatmeal, eggs, or yogurt.
12:30 - 12:45 $ Take a short walk to the university campus.
12:45 - 13:00 $ Arrive at the university and prepare for classes.
13:00 - 13:45 $ Attend classes and take notes.
13:45 - 14:00 $ Take a break and review the notes taken in class.
14:00 - 14:10 $ Get ready for the next class.
"""
        result=chat(summary+sHourPlan+sPrompt)
        sEntries=re.findall('(\d+:\d+)\s*-\s*(\d+:\d+)\s\$([^\n]*)',result)
        new_plans=[]
        minimum_time=dt.combine(time.date(),dt.strptime(sEntries[0][0],'%H:%M').time())
        for entry in sEntries:
            start_time=str(dt.combine(time.date(),dt.strptime(entry[0],'%H:%M').time()))
            end_time=str(dt.combine(time.date(),dt.strptime(entry[1],'%H:%M').time()))
            task=entry[2].strip()
            new_plans.append({'start_time':start_time,'end_time':end_time,'task':task})
        self.plan=[entry for entry in self.plan if dt.strptime(entry['end_time'],'%Y-%m-%d %H:%M:%S')<=minimum_time]
        self.plan.extend(new_plans)
        return new_plans[0]

        # text_base = f"""
        # Name:{self.Name} (age: {self.Age})
        # Innate traits: {self.Personality}
        # {self.Summarize}
        # {self.Name} plans to {plan['task']} date. {self.Name} will do the following things in this time period
        # [Example format:
        #  4:00 pm: grab a light snack, such as a piece of fruit, a granola bar, or some nuts.
        #  4:05 pm: take a short walk around his workspace.]
        #  (Precise to {time_granularity.total_seconds() / 60} minutes):
        #
        # """
        #
        # request_result = chat(text_base)
        #
        # # a sample
        # # request_result = """
        # # 9:00 am: Wake up, take a shower and get ready for the day.
        # #  9:15 am: Eat a healthy breakfast such as oatmeal, eggs, or yogurt.
        # #  9:30 am: Take a short walk to the university campus.
        # #  9:45 am: Arrive at the university and prepare for classes.
        # #  10:00 am: Attend classes and take notes.
        # #  10:45 am: Take a break and review the notes taken in class.
        # #  11:00 am: Get ready for the next class.
        # # """
        #
        # pattern = r"((?:\d+:\d+)\s*(?:am|pm)).*:\s*(.+)"
        # matches = re.findall(pattern, request_result)
        # if matches:
        #     plans = []
        #     for i in range(len(matches)):
        #         match = matches[i]
        #         try:
        #             # task = match[1]  # this neglected the time information, disposed
        #             task = match[1]  # get the whole string, including the time info as the tast str
        #             start_time = datetime.datetime.combine(date
        #                                                    , datetime.datetime.strptime(match[0].replace(" ", ""),
        #                                                                                 "%I:%M%p").time())
        #             if i < len(matches) - 1:
        #                 end_time = datetime.datetime.combine(date
        #                                                      , datetime.datetime.strptime(
        #                         matches[i + 1][0].replace(" ", "")
        #                         , "%I:%M%p").time())
        #             else:
        #                 end_time = plan['end time']
        #             plans.append({
        #                 'task': task,
        #                 'start time': start_time,
        #                 'end time': end_time,
        #             })
        #         except Exception as e:
        #             logging.error(f"Response: {request_result}")
        #             logging.error(e.__traceback__)
        #             logging.error(e.__context__)
        #             # raise Exception("Bad Structure of GPT's response(detailed): Neither 'from...to...' or 'at...' structure")
        #
        #     logging.info(plans)
        #     return plans
        # else:
        #     raise Exception(f"Regex parsing error after requesting plans. Request result: {request_result}")

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

    def add_observation(self, observation):
        self.pending_observation.append(observation)

    def _move_pending_observation(self):
        if len(self.pending_observation) > 0:
            self.incoming_observation.extend(self.pending_observation)
            self.pending_observation = []

    def step(self, current_time:dt):
        """ Call this method at each time frame
        """

        # 产生observation的条件： following reverie, 所有observation都是主体或客体的状态，所以这一步暂时直接交给环境处理。
        # 一类特殊状态，observation of interaction在对话结束给出摘要时才可以确定，此前不能被环境获取。reverie如何在对话开始时生成一个完整对话暂时没看明白
        # short time observation 应该屏蔽掉同主体同状态防止冗余

        logger.debug("Agent {}, Current Time: {}".format(self.state_dict['name'], str(current_time)) )
        
        # # 测试异步
        # if self.state_dict['name'].startswith("A"):
        #     time.sleep(20)
        # logger.debug("Agent {} is done".format(self.state_dict['name']))

        # 为了让agent正常工作，memory, plan, summary不能是空的。因此做一次类似于每日开始时应该进行的初始化
        self.minimal_init(current_time)

        # TODO LIST， 每个人写一个if, 然后if里面用自己的成员函数写，避免大面积冲突。

        # 1. 如果当前正在向openai请求，调过这一步

        self._move_pending_observation()

        # 2. 检查自己当前动作是否需要结束，如果需要，则检查plan，开启下一个动作 （如果下一步没有 fine-grained sroke, 就plan）。 @TODO jingwei
        if self.status_start_time is None: # fixing empty start time
            self.status_start_time = current_time
        if self.status_start_time+datetime.timedelta(self.status_duration)>=current_time:
            # 根据reverie，不产生新观察
            # 对话过程不会随便转状态，因此把对话duration直接设置无限
            next_plan=self.get_next_plan(current_time)
            self.status_start_time=current_time
            self.status=next_plan['status']
            self.status_duration=next_plan['duration']

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

            sContext = f"Summary of relevant context from {self.name}'s memory: " + \
                    ' '.join(sum([self.long_term_memory.query(q,2,current_time) for q in queries],[]))

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
Should {self.name} react to the observation? Say yes or no. 
If yes, tell me about the reaction, omitting the subjective. For example, say 'eating' instead of '{self.name} eats'.  
Is this reaction about saying something? Say yes or no.  
If yes, tell me the content being said in double quotes. 
Does this reaction has a specific target? Say yes or no. 
If yes, tell me the name or how would {self.name} call it. 
Does this reaction need a movement? Say yes or no. 
Also tell me if this reaction terminates {self.name}'s status, Say yes or no. 
Strictly obeying the Output format:
```
1. <Yes/No for being a reaction> : <reaction>
2. <Yes/No for saying something> : <content being said>
3. <Yes/No for targeting> : <target name>
4. <Yes/No for terminating self status> 
```
"""
            result=chat('\n'.join([sSummary,sTime,sStatus,sObservation,sContext,sPrompt]))
            lines=result.split('\n')
            if len(lines)<4:
                logging.warning('abnormal reaction:'+result)
            # line_split=[line.strip().split('$$') for line in lines]
            finds=[line.find('Yes') for line in lines]
            should_react,reaction=finds[0]>=0,lines[0][finds[0]+4:].strip().strip(':').strip()
            should_oral,oral=finds[1]>=0,lines[1][finds[1]+4:].strip().strip(':').strip()
            have_target,target=finds[2]>=0,lines[2][finds[2]+4:].strip().strip(':').strip()
            terminate=finds[3]>=0


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

                if self.environment is not None:
                    self.environment.parse_action(self, target, reaction_content)
                if terminate:
                    self.status=reaction
                    self.status_duration=0
                    self.status_start_time=current_time
                    self.plan_in_detail(current_time)

        # 4. 周期性固定工作 reflect, summary. (暂定100个逻辑帧进行一次) @TODO jingwei

        # 5. 每个帧都要跑下寻路系统。 @TODO xingyu

        return


    
    def step_test(self, current_time:dt):
        """ Call this method at each time frame
        """

        # 产生observation的条件： following reverie, 所有observation都是主体或客体的状态，所以这一步暂时直接交给环境处理。
        # 一类特殊状态，observation of interaction在对话结束给出摘要时才可以确定，此前不能被环境获取。reverie如何在对话开始时生成一个完整对话暂时没看明白
        # short time observation 应该屏蔽掉同主体同状态防止冗余

        # logger.debug("Agent {}, Current Time: {}".format(self.state_dict['name'], str(current_time)) )
        
        # # 测试异步
        # if self.state_dict['name'].startswith("A"):
        #     time.sleep(20)
        # logger.debug("Agent {} is done".format(self.state_dict['name']))

        # 为了让agent正常工作，memory, plan, summary不能是空的。因此做一次类似于每日开始时应该进行的初始化
        # from IPython import embed; embed(header='650')
        self.minimal_init(current_time)


        # TODO LIST， 每个人写一个if, 然后if里面用自己的成员函数写，避免大面积冲突。

        # 1. 如果当前正在向openai请求，调过这一步

        self._move_pending_observation()

        # 2. 检查自己当前动作是否需要结束，如果需要，则检查plan，开启下一个动作 （如果下一步没有 fine-grained sroke, 就plan）。 @TODO jingwei
        if self.status_start_time is None: # fixing empty start time
            self.status_start_time = current_time
        if self.status_start_time+datetime.timedelta(self.status_duration)>=current_time:
            # 根据reverie，不产生新观察
            # 对话过程不会随便转状态，因此把对话duration直接设置无限
            next_plan=self.get_next_plan(current_time)
            self.status_start_time=current_time
            self.status=next_plan['status']
            self.status_duration=next_plan['duration']

        # 3. 检查当前有没有new_observation (或 incoming的interaction 或 invoice), 如果有要进行react, react绑定了reflect和plan的询问。 @TODO zefan
        #    多个observation一起处理，处理过就扔进短期记忆。
        #    短期记忆是已经处理过的observation。

        # 4. 周期性固定工作 reflect, summary. (暂定100个逻辑帧进行一次) @TODO jingwei

        # 5. 每个帧都要跑下寻路系统。 @TODO xingyu


        # # 测试异步
        # if self.state_dict['name'].startswith("A"):
        #     time.sleep(20)
        # logger.debug("Agent {} is done".format(self.state_dict['name']))
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

            sContext = f"Summary of relevant context from {self.name}'s memory: " + \
                    ' '.join(sum([self.long_term_memory.query(q,2,current_time) for q in queries],[]))

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
#                 result=request_GPT.request(''.join([sSummary,sTime,sStatus,sObservation,sContext,sDialog,sPrompt]))
#                 if result.startwith('Yes'):
#                     content= '.'.join(result.split('.')[1:]).strip().split('\n')[0]
#                     new_interaction={'sender':self.name,'content':content}
#                     self.incoming_interactions.append(new_interaction)
#                 else:
#                     if not result.startwith('No'):
#                         logging.warning(logging.WARNING,'abnormal reaction response: '+result)
#                     self.end_interaction(current_time)
        # from IPython import embed; embed(header="in 747")
        
        if len(self.observation)>0:
            #
            sPrompt = f"""
Should {self.name} react to the observation? Say yes or no. 
If yes, tell me about the reaction, omitting the subjective. For example, say 'eating' instead of '{self.name} eats'.  
Is this reaction about saying something? Say yes or no.  
If yes, tell me the content being said in double quotes. 
Does this reaction has a specific target? Say yes or no. 
If yes, tell me the name or how would {self.name} call it. 
Also tell me if this reaction terminates {self.name}'s status, Say yes or no. 
Output format:
```
1. **<Yes/No for being a reaction>**: <reaction>
2. **<Yes/No for saying something>**: <content being said>
3. **<Yes/No for targeting>**: <target name>
4. **<Yes/No for terminating self status>**
```
"""
            result=chat('\n'.join([sSummary,sTime,sStatus,sObservation,sContext,sPrompt]))
            lines=result.split('\n')
            if len(lines)<4:
                logging.warning('abnormal reaction:'+result)
            line_split=[line.strip().split('**') for line in lines]
            should_react,reaction=line_split[0][1], line_split[0][2].strip(':').strip()
            should_oral,oral=line_split[1][1], line_split[1][2].strip(':').strip()
            have_target,target=line_split[2][1], line_split[2][2].strip(':').strip()
            terminate =line_split[3][1]

            if should_react=='Yes':
                if should_oral=='No':
                    reaction_content = reaction+' Also saying: '+oral
                else:
                    reaction_content=reaction
                if not have_target:
                    target=''

                from IPython import embed; embed(header="in 774")
                if self.environment is not None:
                    self.environment.parse_action(self, target, reaction_content)
                if terminate:
                    self.status=reaction
                    self.status_duration=0
                    self.status_start_time=current_time
                    # self.plan_in_detail()

        # 4. 周期性固定工作 reflect, summary. (暂定100个逻辑帧进行一次) @TODO jingwei

        # 5. 每个帧都要跑下寻路系统。 @TODO xingyu


        # 5. 每个帧都要跑下寻路系统。 @TODO xingyu


        return

    def compose_dev(self):
        """ Truncation:  Compose the context feed to large language model in this step (with trucation to avoid overflow of total tokens)
        When finished, this will become depreciated.
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
        agent_playground.reverse()  # recover the original agent_playground

        # finally ground the prompt template
        formatted_prompt = self.prompt_template.format(
            tool_names_and_descriptions=self.tool_names_and_descriptions,
            tool_names=f"[{', '.join(self.tool_names)}]",
            task=self.task,
            agent_playground="".join(agent_playground)
        )

        # TODO: Use all the short term context to compute semnatic embedding -> use cosine similarity to compute the most relevant items and append them to the context

        # MAX_LONG_TERM_MEMORY

        return formatted_prompt

    def step_dev(self):
        """ Single action step"""

        # First update the observation
        self.observe()

        # Fetch incoming interactions
        self.incoming_interactions

        # if exception occurs, retry 3 times at most

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
                action_input_content = json.loads(action_input_content)  # parse str to json

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
