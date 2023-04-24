

# # The color for intermediate result
RESET = "\033[0m"  # reset color output
GREEN = "\033[92m"  # Green text
MAGENTA = "\033[35m"  # Magenta text
RED = "\033[31m"  # Red text
BOLD = "\033[1m"  # Bold text
BLUE = "\033[34m"  # Blue text



def envlog(domain, message):
    '''This is a simple function that will bothe log the message into command line
    and a file for web demo.
    '''

    print(f"{RED}{domain}: {RESET}{message}")