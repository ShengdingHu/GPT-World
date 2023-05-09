import argparse
import os.path
import shutil

import gptworld.utils.logging as logging
from gptworld.create.create import create_world

logger = logging.get_logger(__name__)

if __name__ == '__main__':
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument('--world_instance', '-W', type=str, required=True,
                           help="The path of the world instance (in world_instances/)")
    my_parser.add_argument('--info', '-I', type=str, required=True,
                           help="The basic information of the world you want to create.")
    my_parser.add_argument('--time_delta', '-T', type=int, nargs='?', default=120,
                           help="The time delta between steps in seconds.")

    args = my_parser.parse_args()

    name = args.world_instance
    task = f"Create a world described by the following statements: {args.info}"
    # A typical task
    # task = "Create a neighborhood with some Chinese restaurants (with a cook, tables, chairs, delicious foods), and coffee bar (coffee machine, coffee staff), 711 shop (stocks, drinks, snacks, etc), trees, grass area (with flower, old people, etc), roads (with some cars, bikes), Alice's house and Bob's house (includes some furniture, like sofa, bed, bookshelf, cooker, and their families, a yard with two apple trees, etc), all above should be areas, each task could be a subtask, assign the jobs with lots of details, no overlapping areas. Add some people and animals and plants, evenly distributed. Expect more details. Areas should not overlap with each other."

    output_path = f'../world_instances/{name}'

    if os.path.exists(output_path):
        logger.warning("World instance already exists.")
        ans = input(f"Overwrite existing world instance at {output_path}\n[y/N]")
        if not (ans == 'Y' or ans == 'y'):
            exit(0)
        else:
            shutil.rmtree(output_path)

    time_delta = args.time_delta
    create_world(
        name=name,
        task=task,
        size=[200, 150],
        max_step=40,
        output_path=output_path,
        time_delta=time_delta
    )
