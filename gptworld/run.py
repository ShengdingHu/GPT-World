import argparse
from gptworld.core.environment import GPTWorldEnv
from gptworld.core.agent import GPTAgent

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

    env.run(debug=args.debug, start_time=[2023, 4, 28, 9, 0, 0])


