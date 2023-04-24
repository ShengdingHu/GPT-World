import os
import json


# # The color for intermediate result
RESET = "\033[0m"  # reset color output
GREEN = "\033[92m"  # Green text
MAGENTA = "\033[35m"  # Magenta text
RED = "\033[31m"  # Red text
BOLD = "\033[1m"  # Bold text
BLUE = "\033[34m"  # Blue text


class UILogging:
    """ The log which could be presented to user interface
    """
    def __init__(self, env_path: str):
        self.log_path = os.path.join(env_path, 'uilogging.txt')
        return

    def __call__(self, domain: str, message: str):
        """ This is a simple function that will bothe log the message into command line
        and a file for web demo.
        """
        output_string = f"{domain}|{message}"
        
        with open(self.log_path, 'a') as f:
            f.write(output_string + '\n')

        print(f"{RED}{domain}: {RESET}{message}")
        