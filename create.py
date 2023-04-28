
from gptworld.core.create import EnvironmentCreator

if __name__ == "__main__":
    env_creator = EnvironmentCreator()
    env_creator.add_description("""This is a environment of a debating room. Inside which there are two desks for six debators. Each desk is for three debators of the same side. The two desk face each other. In front of the desk, there are one desk for the host. And there are three chairs for the judges. The room size is 50*50. """)
    env_creator.create()
