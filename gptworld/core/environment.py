import threading
import time
import json
from gptworld.core.agent import GPTAgent
from typing import Dict, List, Tuple
# from gptworld.core.time_system impor, MOVEMENT_TICK
import subprocess
from gptworld.utils.logging import get_logger

logger = get_logger(__file__)
logger.debug = print
logger.info =  print


def run_dev():
    subprocess.run(['npm', 'run', 'dev'], cwd='/Users/hsd/codes/MultiAgent/GPT-World/game/text_grid/frontend', capture_output=True)
    subprocess.run(['python app.py'], cwd='/Users/hsd/codes/MultiAgent/GPT-World/game/text_grid', capture_output=True)


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
        name,
        id,
        size,
        areas,
        objects = None,
        agents = None,
        ):
        # TODO: agents mapping from agent id to AgentThread object


        self.name = name
        self.id = id
        self.size = size
        self.areas = areas
        self.objects = objects
        self.agents = agents
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


    @classmethod
    def from_file(cls, filename):
        logger.debug(filename)
        with open(filename, 'r') as f:
            data = json.load(f)
        return cls(**data)
        
      
    def initialize(self, ):
        import multiprocessing

        
        process = multiprocessing.Process(target=run_dev)
        process.start()

        logger.info("View the demo at locathost:5173")


        # process = subprocess.run(['npm', 'run', 'dev'], 
        # cwd='/Users/hsd/codes/MultiAgent/GPT-World/game/game-vite/game-try-vite/',
        # )



        




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
        environment = None

        return environment

    def load_from_file(self, rootfile):
        with open(f"{rootfile}", 'r') as fenv:
            self.environent = json.load(fenv)
        from IPython import embed; embed()

        # create_agent
        for obj in self.environent['object']:
            if obj['id'].startswith('a'):
                agent = Agent(obj['id'])
            elif obj['id'].startswith('o'):
                object_agent = Agent(obj['id'])
        
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
        
        agent = Agent(state_dict=agent_state_dict, mode="auto")
        self.agents["agent.name"] = agent

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

    def step(self, **kwargs):
        """ For each time frame, call step method for agents
        """

        self.movement_manager.start()

        while self.operational:
            time.sleep(1)
            for agent in self.agents:
                # run agent as thread
                thread = threading.Thread(target=agent.step)
                thread.start() 
            
            # prompt user to input control signal (in case they want to suspand the server)
            command = input("Stop? [y]=stop and save all states")
            if command == "y":
                self.operational = False
        
        # TODO: save the state of all agents to dump files

        # TODO: if necessary, send the agents dump files to user..

        self.movement_manager.join()

        return
    

if __name__ == "__main__":
    # TODO: add some arguments
    env = Environment()
    dirname = 'test_env0'
    env.load_from_file(f"static_files/{dirname}/environment.json")
    env.run()
