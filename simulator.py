import threading
import time
import json
from agent.agent import Agent
from typing import Dict, List, Tuple


THINKING_TICK = 60 # for each agent thread, normally, sleep 60 seconds after 1 thinking operation
MOVEMENT_TICK = 10 # for movement management thread, which in charge of managing grid update, sleep 10 seconds after 1 grid update


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

            time.sleep(THINKING_TICK)
        
        return


class MovementManagement(threading.Thread):
    """ Manage Movements of All Agents
    """
    def __init__(self, grid: Dict[Tuple[int, int], str], agents: Dict[str, AgentThread]):
        self.agents = agents
        self.grid = grid

        # TODO: read VelocityUpperBound for each agent
        
        # TODO: add more ...

        return
    
    def run(self):
        """ The life cycle function
        """
        while True:
            # TODO: for each agent, update its position using its movement status like VelocityUpperBound and MovementTargetLocation, choose the maximum velocity and the best direction, update its location
            for agent in self.agents:
                if not agent.is_moving:
                    continue
                velocity_upper_bound = agent.velocity_upper_bound
                movement_target_location = agent.movement_target_location
                # TODO: calculate the best direction & update the position

            time.sleep(MOVEMENT_TICK)

        return


class Environment:
    """ The envirnment simulator
    Maintain a pool of all AgentThread
    """
    def __init__(self):
        # TODO: maintain proper variables

        # TODO: agents mapping {id:str -> obj:AgentThread}
        self.agents: Dict[str, AgentThread] = {} 

        # TODO: build grid
        self.grid: Dict[Tuple[int, int], str] = {}

        self.movement_manager = MovementManagement(self.grid, self.agents)

        return
    
    def load_agent(self, **kwargs):
        """ Load an agent from a dump file
        """
        # TODO: load agent from a dump file, the format will approximately be a JSON formatted file? then add to self.agents
        agent_state_dict = {}
        with open("./general_agent/general_agent_format.json", "r") as f:
            agent_state_dict = json.load(f)
        
        return
    
    def message_passing(self, receiver: str):
        """ For an agent thread to invoke, in order to call another agent thread
        """
        # TODO: implement the message passing
        # maybe we need to use thread communication
        return
    
    def run(self, **kwargs):
        """ Run all agents as threads
        """
        # TODO: add details
        for agent in self.agents:
            agent.start()
        
        # TODO: start movement manager
        self.movement_manager.start()

        # TODO: join all threads
        self.movement_manager.join()
        for agent in self.agents:
            agent.join()
        
        return
    
