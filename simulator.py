import threading
import time
import json
from agent.agent import Agent
from typing import Dict


TICK = 60 # sleep 1 minute after 1 operation


class AgentThread(threading.Thread, Agent):
    """ In our world envirnment, each agent will reside in a thread. 
    A thread has a sleep interval (sleep 1 minute after 1 action)
    If other agent thread sends an action, the thread will come back to live immediately.
    """
    def __init__(self, agent_state_dict: Dict):
        threading.Thread.__init__(self)
        Agent.__init__(self, **agent_state_dict)

    def run(self):
        """ The life cycle function
        """
        while True:
            # TODO: come back to life if receive a signal from other agents
            # TODO: more details

            # ...
            self.action()
            # ...

            time.sleep(TICK)
        
        return


class Environment:
    """ The envirnment simulator
    Maintain a pool of all AgentThread
    """
    def __init__(self):
        # TODO: maintain proper variables

        # TODO: agents mapping {id:str -> obj:AgentThread}
        self.agents = {} 

        return
    
    def load_agent(self, **kwargs):
        """ Load an agent from a dump file
        """
        # TODO: load agent from a dump file, the format will approximately be a JSON formatted file? then add to self.agents
        agent_state_dict = {}
        with open("./general_agent/general_agent_format.json", "r") as f:
            agent_state_dict = json.load(f)
        
        return
    
    def run(self, **kwargs):
        """ Run all agents as threads
        """
        # TODO: add details
        for agent in self.agents:
            agent.start()
        
        for agent in self.agents:
            agent.join()
        return
    

