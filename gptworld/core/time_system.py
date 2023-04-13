import threading
import time
import json
from agent.agent import Agent
from typing import Dict, List, Tuple


THINKING_TICK = 60 # for each agent thread, normally, sleep 60 seconds after 1 thinking operation
MOVEMENT_TICK = 10 # for movement management thread, which in charge of managing grid update, sleep 10 seconds after 1 grid update

class TimeFrame(object):
    '''Time system, may be need to change to DD/MM/HH/XX:XX format
    '''
    def __init__(self, start_time=0, fake_to_real_ratio=10):
        pass
        self.time = start_time
        while True:
            time.sleep(fake_to_real_ratio)
            self.time += 1

    def get_time(self):
        return self.time


