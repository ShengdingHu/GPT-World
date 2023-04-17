class Server:
    def __init__(self, environment):
        self.envirnment = environment
    
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
    
    def run(self):
        self.envirnment.run()