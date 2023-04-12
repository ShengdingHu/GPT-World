import inspect


class Tool:
    """ bmapi Tool class: all function will be encapulated into Tool object 
    for convenience of all.
    This class is callable, when called, it will execute the corresponding function.
    """
    def __init__(self, func:callable, tool_name:str, tool_description:str="", tool_type:str="normal"):
        """ Store the function, description, and tool_name in a class to store the information
        """
        self.func = func
        if tool_description == "":
            self.tool_description = f"{inspect.signature(func)} : {func.__doc__}"
        else:
            self.tool_description = tool_description
        self.tool_name = tool_name
        self.tool_type = tool_type
    
    def __call__(self, *args, **kwargs):
        """ When the instance called, this method will run
        """
        return self.func(*args, **kwargs)


def as_tool(tool_name: str, tool_type: str="normal") -> Tool:
    """ Convert a function as a bmapi tool function, return a callable Tool
        Usage 1:
        @as_tool("weather")
        def get_weather_today(location: str) -> str:
            ''' get_weather_today(location: str) -> None: get today's weather forcast at given location.
            '''
            return "today is sunny!"
        Will actually yield:
        tool = Tool(get_weather_today, "weather")
        which is a callable object, when called, the original function will be called.
        Usage 2:
        @as_tool("submit_work", "finish")
        def submit_file():
            ''' if you think you have completed the task, call this function to submit your work.
            '''
            return "the work has been submitted"
        You will define this function as a finish tool, after this tool is called, the chain will temrinate.
    """
    def decorator(func: callable) -> Tool:
        """ The original decorator, return wrapper
        """
        tool = Tool(func=func, tool_name=tool_name, tool_type=tool_type)
        print(f"[system]: as tool: {tool_name}")
        return tool # return a callable class instead of a function
    return decorator # return a callable class instead of a function
