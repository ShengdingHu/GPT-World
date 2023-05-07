import threading
import time
import json
from gptworld.core.agent import GPTAgent
from gptworld.core.object import GPTObject, GPTEnvObject
from typing import Dict, List, Tuple
# from gptworld.core.time_system impor, MOVEMENT_TICK
import subprocess

from gptworld.utils.uilogging import UILogging
import os
import datetime
from gptworld.models.openai_api import chat
import re
from gptworld.utils.prompts import load_prompt

import gptworld.utils.logging as logging
logger = logging.get_logger(__name__)


# Use the os module to get the absolute dir path of the current file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


# def run_backend():
#     subprocess.run(['python app.py'], cwd=f'{CURRENT_DIR}/../../io', capture_output=True, shell=True)

# def run_frontend():
#     subprocess.run(['npm run --silent dev'], cwd=f'{CURRENT_DIR}/../../io/frontend', capture_output=True, shell=True)




class GPTWorldEnv:
    """ The envirnment simulator
    Maintain a pool of all AgentThread
    """
    def __init__(self, 
        env_json,
        file_dir,
        clear_memory=False
        ):
        # TODO: agents mapping from agent id to AgentThread object

        self.env_json = env_json
        self.file_dir = file_dir
        self.uilogging = UILogging(file_dir)

        self.agents, self.objects = {}, {}

        self.clear_memory=clear_memory

        self.load_objects_and_agents()
        
        logger.info("Complete environment initialization.")
        
        # TODO: grid mapping from position tuple to agent id
        # self.grid: Dict[Tuple[int, int], str] = {}

        # TODO: movement manager thread object
        # self.movement_manager = MovementManagementThread(self.grid, self.agents)

        # TODO: control mode mapping from agent id to mode (either 'auto' or 'human')
        # self.control_mode: Dict[str, str] = {}

        pass


    def get_elem_by_id(self, id):
        if id.startswith("o"):
            obj = self.env_json['objects'].get(id, {})
            if obj.get('engine', '') == "object":
                return self.objects[id].name
            else:
                return obj['name']
        elif id.startswith("a"):
            return self.agents[id].name
        elif id.startswith("e"):
            return self.env_json['areas'][id]['name']

    def broadcast_observations(self, agent, targets, content=""):
        logger.debug(f"Environment receives action: {agent.name} -> {targets} : {content}")

        EnvironmentPrompt_template = load_prompt(self.file_dir, key='broadcast_observations')
        number = 1
        agents_and_objects = "["

        for a_id in self.agents:
            ag = self.agents[a_id]
            if ag.eid == agent.eid and a_id != agent.id:
                agents_and_objects += f"{ag.name} (location: {ag.location}),"
                number += 1
        for o_id in self.objects:
            obj = self.objects[o_id]
            if obj.eid == agent.eid and o_id != agent.id:
                agents_and_objects += f"{obj.name} (location: {ag.location}),"
                number += 1
        
        agents_and_objects += "]"

        EnvironmentPrompt = EnvironmentPrompt_template.format(agents_and_objects=agents_and_objects, name=agent.name, targets=targets, content=content)
        
        result = chat(EnvironmentPrompt, stop="Finish_Broadcast")

        logger.debug(f"Candidate Broadcast Target: {agents_and_objects}\n Env broadcast the following content: {result}")

        lines = result.split("\n")
        send_content = {}
        for line in lines:
            sline = line.split(":")
            target, content = sline[0], ":".join(sline[1:])
            try:
                target = re.split(r'\d+\. ', target)[1][3:]
            except:
                continue
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
        


    @classmethod
    def from_file(cls, file_dir, file_name ="environment.json",clear_memory=False):
        logger.info(f"Loading environment from {file_dir}")
        with open(os.path.join(file_dir, file_name), 'r') as f:
            data = json.load(f)
        return cls(**{"env_json": data, "file_dir": file_dir,"clear_memory":clear_memory})
        
      
    def initialize_web(self, ):
        return RuntimeError("Disabled")
        import multiprocessing
    
        # process_backend = multiprocessing.Process(target=run_backend)
        # process_frontend = multiprocessing.Process(target=run_frontend)
        # process_backend.start()
        # process_frontend.start()

        # logger.critical("\n\033[1m\033[93m"+"-"*20 + "\nView your little world at http://localhost:5001\n" + "-"*20)

        return

    def get_neighbor_environment(self, agent_id :str = None, critical_distance = -1):
        '''Provide the local environment of the location.

        Args:
            agent_id (:obj:`str`): The agent id, to filter the agent itself
            critical_distance (:obj:`int`): A distance that counts as the neighborhood.
        
        Returns:
            :text: the observation text. E.g., Now you are at fields. There are tractor, Bob, around you.'
        '''
        if critical_distance == -1:
            critical_distance = 999999999

 
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
        template = "{} is at location {} of {}, status: {}."
        for obj_id in objects_within_distance:
            if obj_id.startswith('a'):
                agent = self.agents[obj_id]
                filled = template.format(agent.name, agent.location, at_area,  agent.status)
                observations.append(filled)
            elif obj_id.startswith('o') and  obj_id in self.objects:
                agent = self.objects[obj_id]
                filled = template.format(agent.name, agent.location, at_area, agent.status)
                observations.append(filled)


        return observations
    
    # def get_observation_text(self, observation):
    #     prompt_template = "Now you are at {}. There are {} around you."
    
    #     object_text = []
    #     for obj_id in observation['objects_within_distance']:
    #         object_text.append(self.env_json['objects'][obj_id]['name'])
    #     object_text = ", ".join(object_text) if len(object_text) > 0 else "nothing"

    #     prompt = prompt_template.format(observation['agent_location'], object_text)
    #     return prompt


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
                self.agents[obj_id] = GPTAgent(os.path.join(self.file_dir, '{}.json'.format(obj_id)), environment=self,clear_memory=self.clear_memory)
            elif obj['id'].startswith('o') and obj['engine'] == 'object':
                self.objects[obj_id] = GPTObject(os.path.join(self.file_dir, '{}.json'.format(obj_id)), environment=self)
            elif obj['id'].startswith('o') and obj['engine'] == 'environment':
                # self.objects[obj_id] = GPTEnvObject(obj, environment=self)
                pass

            
            

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

    def get_invoice(self, ):
        INVOICE_PATH = os.path.join(self.file_dir, "invoice.txt")
        if os.path.exists(INVOICE_PATH):
            with open(INVOICE_PATH, 'r') as fp:
                incoming_invoice = fp.read()
                logger.critical("find invoice: {}".format(incoming_invoice))
                if incoming_invoice:
                    self.broadcast_invoice(incoming_invoice)
        else:
            logger.warning("No invoice files")
        
    def send_system_message(self, id, message):
        invoice_prompt = "Here is a system message that is of highest priority. Who observe it should strict follows the message until it is completed: "
        if id.startswith('a'):
                self.agents[id].set_invoice(invoice_prompt + message)
        elif id.startswith('o'):
                self.objects[id].set_invoice(invoice_prompt + message)
        logger.debug(f"broadcast {message} to {id}")


    def broadcast_invoice(self, incoming_invoice):
        objectlist = [(aid, self.agents[aid].name) for aid in self.agents] + [(oid, self.objects[oid].name) for oid in self.objects]  
        prompt_template = load_prompt(self.file_dir, key='system_message_broadcast')
        prompt = prompt_template.format(objectlist=objectlist, system_message=incoming_invoice)

        return_value = chat(prompt, stop="END")
        return_value = [x.strip() for x in return_value.split("\n")]
        for line in return_value:
            try:
                eval("self."+line)
            except:
                logger.warning("Send system message error: {}".format(line))
                continue

    def get_system_message(self, ):
        system_message = self.env_json.get('system_message', {}).get(datetime.datetime.strftime(self.current_time, "%Y-%m-%d %H:%M:%S"), '')
        if system_message != '':
            logger.critical("find system_message: {}".format(system_message))
            self.broadcast_invoice(system_message)

    def fetch_elem_info(self, typeset=['a','o'], return_info='name'):
        elems = {}
        if 'o' in typeset:
            for id, info in self.env_json['objects'].items():
                elems[id] = info[return_info]
        elif 'a' in typeset:
            for id, info in self.env_json['agents'].items():
                elems[id] = info[return_info]
        return elems

    def step(self, debug=False):
        """ For each time frame, call step method for agents
        """

        # self.movement_manager.start()
        logger.info(f"New environment step starts. Current environment time: {self.current_time}")

        thread_pool = []
        self.get_invoice()
        self.get_system_message()

        # sync between frames
        for agent_id in self.agents:
            agent = self.agents[agent_id]
            # run agent as thread
            if debug:
                agent.sync(self.current_time)
            else:
                thread = threading.Thread(target=agent.sync, args=(self.current_time,))
                thread_pool.append(thread)
                thread.start() 
        
        for obj_id in self.objects:
            object = self.objects[obj_id]
            if isinstance(object, GPTObject):
                if debug:
                    object.sync(self.current_time)
                else:
                    thread = threading.Thread(target=object.sync, args=(self.current_time,))
                    thread_pool.append(thread)
                    thread.start() 
        
        if not debug:
            for thread in thread_pool:
                thread.join()

        # perform step
        for agent_id in self.agents:
            agent = self.agents[agent_id]
            # run agent as thread
            if debug:
                agent.step(self.current_time)
            else:
                thread = threading.Thread(target=agent.step, args=(self.current_time,))
                thread_pool.append(thread)
                thread.start()
                # 5. 每个帧都要跑下寻路系统。
                move_thread = threading.Thread(target=agent.move_async, args=())
                thread_pool.append(move_thread)
                move_thread.start()
        
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
    
    def run(self, debug=False):
        """The main loop 
        """
        env_time_delta = int(self.env_json['time_delta'])
        start_time = datetime.datetime.strptime(self.env_json['current_time'], "%Y-%m-%d %H:%M:%S")
        
        self.current_time = start_time
        while True:
            self.step(debug=debug)
            self.current_time += datetime.timedelta(seconds = env_time_delta)
    
