import argparse
from gptworld.core.environment import GPTWorldEnv
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='If enabled, we will not use thread, so that debug becomes easier.')
    parser.add_argument('--world_instance',"-W", type=str, required=True, help='The path of the world instance (in world_instances/)')
    parser.add_argument('--continue_run', '-C', action='store_true', help='start from the initial state of the environment, or continue to run from with an existing .world_instance.running directory. ') 
    # clear_memory may be legacy?
    parser.add_argument('--clear_memory',action='store_true', help='Clear the old memory file before starting environment to prevent conflicting memory') 

    args = parser.parse_args()

    # copy the files of the world_instance into a temperary runing folder
    import shutil
    static_dir = f"world_instances/{args.world_instance}/"
    running_dir = f"world_instances/.{args.world_instance}.running/"
    if os.path.exists(running_dir):
        if not args.continue_run:
            ans = input(f"Overwrite existing runing world instance at {running_dir}\nInput Y to continue,  N to abort:")
            if ans == 'Y':
                shutil.rmtree(running_dir)
                shutil.copytree(static_dir, running_dir)
            else:
                exit(0)
    else:
        shutil.copytree(static_dir, running_dir)

    # Create an instance of the environment
    env = GPTWorldEnv.from_file(running_dir,clear_memory=args.clear_memory)

    env.run(debug=args.debug)

