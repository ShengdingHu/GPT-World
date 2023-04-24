import threading
import time
import json
from gptworld.core.agent import GPTAgent
from gptworld.core.object import GPTObject, GPTEnvObject
from typing import Dict, List, Tuple
# from gptworld.core.time_system impor, MOVEMENT_TICK
import subprocess
from gptworld.utils.logging import get_logger
import os
import datetime
from gptworld.models.openai import chat
import re


logger = get_logger(__file__)
logger.debug = print
logger.info =  print

# Use the os module to get the absolute dir path of the current file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))





def run_dev():
    subprocess.run(['npm', 'run', 'dev'], cwd=f'{CURRENT_DIR}/../../game/text_grid/frontend', capture_output=True,shell=True)
    subprocess.run(['python app.py'], cwd=f'{CURRENT_DIR}/../..//game/text_grid', capture_output=True,shell=True)


def action_parser():
    """ Parser parses natural language to identify the broadcasting target(s).
        Broadcast the message to the observation of the relevant agent(s).
    """

    prompt = """
    Example 1
    Thought:
    I need to send a text message to my parents and tell them that I am fine
    Knowledge:
    Relationship=["Father": "Lao Wang", "Mother": "Lao Li"]
    API Call:
    "Lao Wang", "messaging", "I'm fine"
    "Lao Li", "messaging", "I'm fine"

    Example 2:
    Thought:
    I want to inform my friends that I want to have a party on Sunday
    Knowledge:
    Friend: ["Little A", "Little B", "Little C"]
    API Call:
    "Little A", "messaging", "I want to have a party on Sunday"
    "Little B", "messaging", "I want to have a party on Sunday"
    "Little C", "Text message", "I want to have a party on Sunday"

    Have you discovered the pattern? The first is the only existing named entity (not a reference), the second is the action, and the third is the specific content. If the action is given, it is best to choose from it, if you have other unprovided actions, you could use "misc". The content may not be provided.

    Here is a new scenario:
    Thought:
    I want to start the car
    Knowledge:
    ParentElement: ["Das Auto A100": "start engine", "get off", "open windows", "misc"]
    API Call:
    """
    
    return


class GPTWorldEnv:
    """ The envirnment simulator
    Maintain a pool of all AgentThread
    """
    def __init__(self, 
        env_json,
        file_dir,
        # name,
        # id,
        # size,
        # areas,
        # objects = None,
        # agents = None,
        ):
        # TODO: agents mapping from agent id to AgentThread object

        self.env_json = env_json
        self.file_dir = file_dir

        self.agents, self.objects = {}, {}

        self.load_objects_and_agents()
        
        logger.debug("Initialize Complete!")

        

        # TODO: grid mapping from position tuple to agent id
        # self.grid: Dict[Tuple[int, int], str] = {}

        # TODO: movement manager thread object
        # self.movement_manager = MovementManagementThread(self.grid, self.agents)

        # TODO: control mode mapping from agent id to mode (either 'auto' or 'human')
        # self.control_mode: Dict[str, str] = {}

        # control if operational
        # self.operational = True
        pass

    def get_area_name(self, eid):
        return self.env_json['areas'][eid]['name']

    def parse_action(self, agent, targets, content=""):
        logger.debug(f"Environment receives action: {agent.name} -> {targets} : {content}")

        EnvironmentPrompt = f"""You are simulating an environment. When an action happens
        in your environment, you should paraphrase the action to agents and objects in 
        your environment. In 
        your environment there are the following agent:
        """

        number = 1
        for a_id in self.agents:
            ag = self.agents[a_id]
            if ag.eid == agent.eid and a_id != agent.id:
                EnvironmentPrompt += f"{number}. To {ag.name}: content\n"
                number += 1
        for o_id in self.objects:
            obj = self.objects[o_id]
            if obj.eid == agent.eid and o_id != agent.id:
                EnvironmentPrompt += f"{number}. To {obj.name}: content\n"
                number += 1
            

        EnvironmentPrompt += f"\nNow please paraphrase the following action: ```{agent.name} -> {targets} : {content}``` to each of these agents and objects. Please paraphrase using the following format: \n1. To XXX: XXX\n2. To XXX: XXX"
        
        result = chat(EnvironmentPrompt)

        logger.debug(f"Env broadcast the following content: {result}")

        lines = result.split("\n")
        send_content = {}
        for line in lines:
            sline = line.split(":")
            target, content = sline[0], ":".join(sline[1:])
            target = re.split(r'\d+\. ', target)[1][3:]
            send_content[target] = content

        for a_id in self.agents:
            ag = self.agents[a_id]
            if ag.eid == agent.eid and a_id != agent.id:
                if ag.name in send_content:
                    ag.add_observation(send_content[ag.name])
  
        for o_id in self.objects:
            obj = self.objects[o_id]
            if obj.eid == agent.eid and o_id != agent.id:
                if obj.name in send_content:
                    if isinstance(obj, GPTObject):
                        obj.add_observation(send_content[obj.name])
        

        pass


    @classmethod
    def from_file(cls, file_dir, file_name ="environment.json"):
        logger.debug(file_dir)
        with open(os.path.join(file_dir, file_name), 'r') as f:
            data = json.load(f)
        return cls(**{"env_json": data, "file_dir": file_dir})
        
      
    def initialize_web(self, ):
        import multiprocessing

        
        process = multiprocessing.Process(target=run_dev)
        process.start()

        logger.info("-"*20 + "\nView the demo at localhost:5173\n" + "-"*20)


    def get_neighbor_environment(self, agent_id :str = None, critical_distance = 50):
        '''Provide the local environment of the location.

        Args:
            agent_id (:obj:`str`): The agent id, to filter the agent itself
            critical_distance (:obj:`int`): A distance that counts as the neighborhood.
        
        Returns:
            :text: the observation text. E.g., Now you are at fields. There are tractor, Bob, around you.'
        '''

 
        location = self.env_json['objects'][agent_id]['location']
        env_id = self.env_json['objects'][agent_id]['eid']

        at_area = self.env_json['areas'][env_id]['name']
        
        # Find objects within the agent's reach in distance
        objects_within_distance = []
        
        for obj_id, obj in self.env_json['objects'].items():
            if obj_id != agent_id:
                obj_location = obj['location']
                distance = abs(obj_location[0] - location[0]) + abs(obj_location[1] - location[1])
                if distance <= critical_distance and env_id == obj['eid']:
                    objects_within_distance.append(obj_id)
        
        observations = []
        template = "{} is {}."
        for obj_id in objects_within_distance:
            if obj_id.startswith('a'):
                agent = self.agents[obj_id]
                filled = template.format(agent.name, agent.status)
            elif obj_id.startswith('o'):
                agent = self.objects[obj_id]
                filled = template.format(agent.name, agent.status)
            observations.append(filled)


        # # Generate the observation
        # observation = {
        #     "agent_location": at_area,
        #     "objects_within_distance": objects_within_distance
        # }
        # observation_text = self.get_observation_text(observation)

        return observations
    
    def get_observation_text(self, observation):
        prompt_template = "Now you are at {}. There are {} around you."
    
        object_text = []
        for obj_id in observation['objects_within_distance']:
            object_text.append(self.env_json['objects'][obj_id]['name'])
        object_text = ", ".join(object_text) if len(object_text) > 0 else "nothing"

        prompt = prompt_template.format(observation['agent_location'], object_text)
        return prompt


    def show(self):
        '''Show the current status of this environment in a table
        '''
        return
    
    def create_by_prompt(self, message):
        '''Create the environment through user provided message.

        Args: 
            message (:obj: List[Dict]) a message like [{'role': 'user', 'content': 'hello'},]
        
        '''
        environment = None

        return environment

    def load_objects_and_agents(self):

        # create_agent
        for obj_id, obj in self.env_json['objects'].items():
            if obj_id.startswith('a'):
                self.agents[obj_id] = GPTAgent(os.path.join(self.file_dir, '{}.json'.format(obj_id)), environment=self)
            elif obj['id'].startswith('o') and obj['engine'] == 'object':
                self.objects[obj_id] = GPTObject(os.path.join(self.file_dir, '{}.json'.format(obj_id)), environment=self)
            elif obj['id'].startswith('o') and obj['engine'] == 'environment':
                self.objects[obj_id] = GPTEnvObject(obj, environment=self)

            
            

    def save(self, ):
        '''Save the environment to a database.
        '''
        return

    def load_agent(self, agent_id, **kwargs):
        """ Load an agent from a dump file
        """
        # TODO: load agent from a dump file, the format will approximately be a JSON formatted file? then add to self.agents
        agent_state_dict = {}
        with open("./agent_format.json", "r") as f:
            agent_state_dict = json.load(f)
        
        agent = GPTAgent(state_dict=agent_state_dict, mode="auto")

        return
    
    def action_handler(self, sender: GPTAgent, receiver: str, content: str):
        """ For an agent thread to invoke, in order to call another agent thread
        """
        # TODO: implement the message passing
        receiver_agent = self.agents.get(receiver, None)
        if receiver_agent is None:
            # fuzzy match
            pass
        else:
            receiver_agent.incoming_interactions.append({"sender": sender, "content": content})
        return

    def step(self, debug=False):
        """ For each time frame, call step method for agents
        """

        # self.movement_manager.start()

   

        thread_pool = []

        for agent_id in self.agents:
            agent = self.agents[agent_id]
            # run agent as thread
            if debug:
                agent.step(self.current_time)
            else:
                thread = threading.Thread(target=agent.step, args=(self.current_time,))
                thread_pool.append(thread)
                thread.start() 
        
        for obj_id in self.objects:
            object = self.objects[obj_id]
            if isinstance(object, GPTObject):
                if debug:
                    object.step(self.current_time)
                else:
                    thread = threading.Thread(target=object.step, args=(self.current_time,))
                    thread_pool.append(thread)
                    thread.start() 
            

        if not debug:
            for thread in thread_pool:
                thread.join()

        
        
            # 同步操作  @TODO bokai

            

        
        # TODO: save the state of all agents to dump files

        # TODO: if necessary, send the agents dump files to user..

        return
    
    def run(self, start_time=[2023, 4, 1, 7, 0, 0], debug=False):
        """The main loop 
        """
        realworld_time_delta = 8
        env_time_delta = 10
        
        self.current_time = datetime.datetime(*start_time)
        while True:
            time.sleep(realworld_time_delta)
            self.step(debug=debug)
            self.current_time += datetime.timedelta(seconds = env_time_delta)
    

if __name__ == "__main__":
    # TODO: add some arguments
    env = Environment()
    dirname = 'test_env0'
    env.load_from_file(f"static_files/{dirname}/environment.json")
    env.run()
