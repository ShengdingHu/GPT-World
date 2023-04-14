import threading
import time
import json
from agent.agent import Agent
from typing import Dict, List, Tuple
from gptworld.core.time_system import THINKING_TICK, MOVEMENT_TICK

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