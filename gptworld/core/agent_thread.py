import threading
import time
import json
import random
from typing import Dict, List, Tuple
from gptworld.core.time_system import THINKING_TICK, MOVEMENT_TICK
from gptworld.core.environment import Environment
from gptworld.core.agent import Agent


"""
AgentThread class implements the interaction between:
Agent <-> Other Agents
Agent <-> Environment
Agent <-> Physical System
Agent <-> Time System
"""


class AgentThread(threading.Thread, Agent):
    """ In our world envirnment, each agent will reside in a thread. 
    A thread has a sleep interval (sleep 1 minute after 1 action)
    If other agent thread sends an action, the thread will come back to live immediately.
    """
    def __init__(self, agent_state_dict: Dict, mode: str='auto'):
        """ agent_state_dict: Dict, all information about the agent
        mode: either 'auto' or 'human', currently default to auto
        """ 

        # By default, the agent will be driven by large language model
        self.mode = mode

        # By default, the agent will not be mounted to any environment.
        self.environment = None 

        # Initialize thread
        threading.Thread.__init__(self)
        
        # Initialize the agent ontology
        Agent.__init__(self, **agent_state_dict)

        # Whether the agent is thinking (blocking)
        self.blocking = False

        return
    
    def mount_to_environment(self, environment: Environment, environment_id: str = None, location: List[int, int] = None):
        """ Place the agent into the environment, and register the environment 
        into a member variable of the agent.
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

    def interact_handler(self, content: str, sender: str):
        """ Handle the interaction request from other agents (subjective or objective or environment)
        """
        self.interaction.append({"sender": sender, "content": content})
        return
        
    def start(self):
        """ Call this method at each time frame
        """
        # TODO: if the agent is thinking : 博凯
        if self.blocking:
            pass
            
        # TODO: if agent is 'objective' : 博凯
        if self.type == 'objective':
            pass
        
        # if no interaction in interaction_queue : 博凯
        if self.observation_queue == []:
            pass
        
        # Acquire the lock
        self.blocking = True

        try:
            self.action()
        except:
            # TODO: handle exception
            pass
        
        # Release the lock
        self.blocking = False

        return
