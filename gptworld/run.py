# A main file that activate the environent and the agent and let the game goes automatically. 

# Import necessary modules

if __name__ == "__main__":
    import argparse
    from gptworld.core.environment import GPTWorldEnv
    from gptworld.core.agent import GPTAgent
    
    # Create an argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--no_web', action='store_true', help='Starts a new subprocess to start a webpage')
    parser.add_argument('--debug', action='store_true', help='If enabled, we will not use thread, so that debug becomes easier.')
    args = parser.parse_args()

    # Create an instance of the environment
    env = GPTWorldEnv.from_file("static_files/alice_home/")

    if not args.no_web:
        env.initialize_web() # this start a new subprocess to start a webpage.


    # Create an instance of the agent
    # agent1 = GPTAgent.from_file("static_files/test_env0", "a_001.json")
    # agent2 = GPTAgent.from_file("static_files/test_env0", "a_002.json")

    environment_text = env.get_neighbor_environment(agent_id='a_001')

    print(environment_text)


    # env.mount_agent(agent1)
    # env.mount_agent(agent2)

    env.run(debug=args.debug)


