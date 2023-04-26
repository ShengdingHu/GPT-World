import os
import logging
from datetime import datetime
import colorlog

BLACK="\033[30m"
RED="\033[31m"
YELLOW="\033[33m"
BLUE="\033[34m"
MAGENTA="\033[35m"
CYAN="\033[36m"
WHITE="\033[37m"
GREY="\033[90m"
RESET = "\033[0m"  # reset color output
GREEN = "\033[92m"  # Green text
BOLD = "\033[1m"  # Bold text


color_map = {
    "DEBUG": "\033[2m"
}

def get_logger(name: str, level: int = None, log_dir: str = None, file_name: str = None):
    """Function to setup a logger for the gptworld package"""
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../logs") # use current working directory if log_dir not specified
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

    if file_name is None:
        now = datetime.now()
        file_name = now.strftime("%Y-%m-%d_%H-%M-%S.log")  # use current date and time as filename if not specified
    
    if level is None:
        level = os.environ.get('GPTWORLD_LOG_LEVEL', 'INFO').upper()

    log_file = os.path.join(log_dir, file_name)

    if level == "DEBUG":
        formatter_string = "\033[2m%(asctime)s [%(levelname)s] (GPTWorld)%(module)s:%(lineno)d >> %(message)s"
    if level == "INFO":
        formatter_string = "\033[1m%(asctime)s \033[1;37m[%(levelname)s]\033[0m \033[1;36m(GPTWorld)%(module)s:%(lineno)d\033[0m >> %(message)s"



    # create formatter with colorlog
    formatter_cmd = colorlog.ColoredFormatter(
        '[%(log_color)s%(levelname)s|%(name)s:%(lineno)d%(reset)s] %(asctime)s >> %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        },
        reset=True,
        style='%'
    )

    formatter = logging.Formatter(
        '[%(levelname)s|%(name)s:%(lineno)d] %(asctime)s.%(msecs)03d >> %(message)s'
    )

    
    # add file handler
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setFormatter(formatter)

    # add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter_cmd)

    logger = logging.getLogger(name)

    
    logger.setLevel(level)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
