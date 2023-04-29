import argparse
from gptworld.core.environment import GPTWorldEnv


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='If enabled, we will not use thread, so that debug becomes easier.')
    parser.add_argument('--world_instance',"-W", type=str, required=True, help='The path of the world instance (in world_instances/)')
    parser.add_argument('--clear_memory',action='store_true', help='Clear the old memory file before starting environment to prevent conflicting memory')

    args = parser.parse_args()

    # Create an instance of the environment
    env = GPTWorldEnv.from_file(f"world_instances/{args.world_instance}/",clear_memory=args.clear_memory)

    env.run(debug=args.debug)


