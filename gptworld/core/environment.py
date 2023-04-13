import threading
import time
import json
from agent.agent import Agent
from typing import Dict, List, Tuple
from gptworld.core.time_system import THINKING_TICK, MOVEMENT_TICK




class Environment:
    """ The envirnment simulator
    Maintain a pool of all AgentThread
    """
    def __init__(self):
        # TODO: maintain proper variables

        # TODO: agents mapping from agent id to AgentThread object
        self.agents: Dict[str, AgentThread] = {} 

        # TODO: grid mapping from position tuple to agent id
        self.grid: Dict[Tuple[int, int], str] = {}

        # TODO: movement manager thread object
        self.movement_manager = MovementManagementThread(self.grid, self.agents)

        # TODO: control mode mapping from agent id to mode (either 'auto' or 'human')
        self.control_mode: Dict[str, str] = {}

        # control if operational
        self.operational = True

        return
    

    def get_neighbor_environment(self, location: Tuple[int]):
        '''Provide the local environment of the location.

        Args:
            location (:obj:`Tuple[int]`): The center of the view point.
        
        Returns:
            :obj: Observation : The observation in the form of a json.
        '''
        observation = {
            "(1, 1)": "Tree",
            "(-1, 2)": "Tree",
            "(-1, 3)": "Water",
        }
        return observation

    def show(self):
        '''Show the current status of this environment in a table
        '''
        return
    
    def create_by_prompt(self, message):
        '''Create the environment through user provided message.

        Args: 
            message (:obj: List[Dict]) a message like [{'role': 'user', 'content': 'hello'},]
        
        '''
        environment = {
            "name": "Happy Farm",
            "id": "e_123456789",
            "content": [
                {"pos":"[(0,0)]", "name":"door", "id": "o_1234567900"},
                {"pos":"[(0,2)]", "name":"tree", "id": "o_12345679q2"},
                {"pos": "[(1,3)-(3,6)]", "name":"house", "id": "e_1234567900"},
            ],
            "host_agent": [
                {"id": "a_1342342", "name": "Alice"},
                {"id": "a_12315235", "name": "Bob"}
            ]
        }

        return environment
    
    def save(self, ):
        '''Save the environment to a database.
        '''
        return

    def run_interact(self, agent, message):
        '''Parser parses natural language to identify the broadcasting target(s).
        Broadcast the message to the observation of the relevant agent(s).
        
        run each agent's react function
        '''
        
        pass

    def load_agent(self, agent_id, **kwargs):
        """ Load an agent from a dump file
        """
        # TODO: load agent from a dump file, the format will approximately be a JSON formatted file? then add to self.agents
        agent_state_dict = {}
        with open("./agent_format.json", "r") as f:
            agent_state_dict = json.load(f)
        
        agent = AgentThread(agent_state_dict=agent_state_dict, mode="auto")
        self.agents["agent.name"] = agent

        return
    
    def message_passing(self, message: Dict, receiver: str):
        """ For an agent thread to invoke, in order to call another agent thread
        """
        # TODO: implement the message passing
        # maybe we need to use thread communication
        return

    def request_handler(self, request):
        """ handle human request (if the agent is controlled by human)
        Not necessary to implement in our first stage
        """
        # TODO: handle human request (if the agent is controlled by human)
        
        response = "ok"
        return response

    def change_agent_control_mode(self, request):
        """ Change the control mode of one agent
        Not necessary to implement in our first stage
        """
        # TODO: users can change the control mode of one agent
        
        response = "ok"
        return response

    def run(self, **kwargs):
        """ Run all agents as threads
        """
        # TODO: add details
        for agent in self.agents:
            agent.start()
        
        # TODO: start movement manager
        self.movement_manager.start()

        # TODO: prompt user to input control signal (in case they want to suspand the server)
        while True:
            command = input("Stop? [y]=stop and save all states")
            if command == "y":
                self.operational = False
        
        # TODO: save the state of all agents to dump files

        # TODO: if necessary, send the agents dump files to user..

        # TODO: join all threads
        self.movement_manager.join()
        for agent in self.agents:
            agent.join()
        
        return
    

    

if __name__ == "__main__":
    # TODO: add some arguments
    env = Environment()
    env.run()
