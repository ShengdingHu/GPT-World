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
        self.elems = {}

        self.clear_memory=clear_memory

        self.load_objects_and_agents()
        
        logger.info("Complete environment initialization.")
        
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

        for id in self.elems:
            el = self.elems[id]
            if el.eid == agent.eid and id != agent.id:
                agents_and_objects += f"{el.name} (location: {el.location}),"
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

        for id in self.elems:
            el = self.elems[id]
            if el.eid == agent.eid and id != agent.id:
                if el.name in send_content:
                    el.add_observation(send_content[el.name])
        


    @classmethod
    def from_file(cls, file_dir, file_name ="environment.json",clear_memory=False):
        logger.info(f"Loading environment from {file_dir}")
        with open(os.path.join(file_dir, file_name), 'r') as f:
            data = json.load(f)
        return cls(**{"env_json": data, "file_dir": file_dir,"clear_memory":clear_memory})
        


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

 
        location = self.elems[agent_id].location
        env_id = self.elems[agent_id].eid

        at_area = self.env_json['areas'][env_id]['name']
        
        # Find objects within the agent's reach in distance
        objects_within_distance = []
        
        for obj_id, obj in self.elems.items():
            if obj_id != agent_id:
                obj_location = obj.location
                distance = abs(obj_location[0] - location[0]) + abs(obj_location[1] - location[1])
                if distance <= critical_distance and env_id == obj.eid:
                    objects_within_distance.append(obj_id)
        
        observations = []
        template = "{} is at location {} of {}, status: {}."
        for obj_id in objects_within_distance:
            agent = self.elems[obj_id]
            filled = template.format(agent.name, agent.location, at_area,  agent.status)
            observations.append(filled)

        return observations


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
                self.elems[obj_id] = self.agents[obj_id]
            elif obj['id'].startswith('o') and obj['engine'] == 'object':
                self.objects[obj_id] = GPTObject(os.path.join(self.file_dir, '{}.json'.format(obj_id)), environment=self)
                self.elems[obj_id] = self.objects[obj_id]
            elif obj['id'].startswith('o') and obj['engine'] == 'environment':
                # self.objects[obj_id] = GPTEnvObject(obj, environment=self)
                pass

            
            

    def save(self, ):
        '''Save the environment to a database.
        '''
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
                self.elems[id].set_invoice(invoice_prompt + message)
        elif id.startswith('o'):
                self.elems[id].set_invoice(invoice_prompt + message)
        logger.debug(f"broadcast {message} to {id}")


    def broadcast_invoice(self, incoming_invoice):
        objectlist = [(id, self.elems[id].name) for id in self.elems]
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

    def fetch_elem_info(self, typeset=['a','o']):
        elems = {}
        for id, elem in self.env_json['objects'].items():
            elems[id] = elem['name']
        return elems


    def step(self, debug=False):
        """ For each time frame, call step method for agents
        """


        self.uilogging("World", "current time: {}".format(self.current_time))

        thread_pool = []
        self.get_invoice()
        self.get_system_message()

        # sync between frames
        for elem_id in self.elems:
            elem = self.elems[elem_id]
            # run agent as thread
            if debug:
                elem.sync()
            else:
                thread = threading.Thread(target=elem.sync, args=())
                thread_pool.append(thread)
                thread.start() 
        
        if not debug:
            for thread in thread_pool:
                thread.join()

        thread_pool = []
        # perform step
        for elem_id in self.elems:
            elem = self.elems[elem_id]
            # run agent as thread
            if debug:
                elem.step(self.current_time)
            else:
                thread = threading.Thread(target=elem.step, args=(self.current_time,))
                thread_pool.append(thread)
                thread.start()
                # The pathfinding system needs to be run for each frame.
        
        if not debug:
            for thread in thread_pool:
                thread.join()
        
        # move
        thread_pool = []
        for elem_id in self.elems:
            elem = self.elems[elem_id]
            move_thread = threading.Thread(target=elem.move_async, args=())
            thread_pool.append(move_thread)
            move_thread.start()
        for thread in thread_pool:
            thread.join()
        
        
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
    
