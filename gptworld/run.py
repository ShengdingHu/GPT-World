import argparse
from gptworld.core.environment import GPTWorldEnv
from gptworld.core.agent import GPTAgent


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--no_web', action='store_true', help='Starts a new subprocess to start a webpage')
    parser.add_argument('--debug', action='store_true', help='If enabled, we will not use thread, so that debug becomes easier.')
    parser.add_argument('--world_instance', type=str, default='', help='The path of the world instance (in world_instances/)')

    args = parser.parse_args()

    # Create an instance of the environment
    env = GPTWorldEnv.from_file(f"static_files/{args.world_instance}/")

    if not args.no_web:
        env.initialize_web() # this start a new subprocess to start a webpage.

    env.run(debug=args.debug)


