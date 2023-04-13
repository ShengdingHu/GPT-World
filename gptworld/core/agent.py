import threading
import time
import json
# from agent.agent import Agent
from typing import Dict, List, Tuple
from gptworld.core.time_system import THINKING_TICK, MOVEMENT_TICK
from gptworld.core.environment import Environment

class AgentThread(threading.Thread, Agent):
    """ In our world envirnment, each agent will reside in a thread. 
    A thread has a sleep interval (sleep 1 minute after 1 action)
    If other agent thread sends an action, the thread will come back to live immediately.
    """
    def __init__(self, agent_state_dict: Dict, mode: str='auto'):
        """ agent_state_dict: Dict, all information about the agent
        mode: either 'auto' or 'human', currently default to auto
        """ 

        self.mode = mode
        threading.Thread.__init__(self)
        Agent.__init__(self, **agent_state_dict)

        return
    
    def read_memory(self, ):
        pass

    def get_observation(self, ):
        '''Use current environment id, and location to get current observation by query the environment's
        get_neighbor_environment function
        '''

        return
    
    def reflection(self, ):
        '''
        '''

        pass

    def plan(self, ):
        '''
        '''
        pass

    def interact(self, ):
        '''
        '''
        self.environment.run_interact()
        

    def set_to_environment(self, environment, environment_id=None, location=None):
        '''Place the agent into the environment, and register the environment 
        into a member variable of the agent.
        '''
        pass


    def action(self, ):
        ''' 
        '''
        pass

    def react(self, message):
        ''' Provide feedback to external stimuli.
        '''
        
    def start(self):
        """ The life cycle function
        """
        while True:
            
            self.action()
                # ...

            # TODO: come back to life if receive a signal from other agents

            # finally sleep for THINKING_TICK
            time.sleep(THINKING_TICK)
        
        return
