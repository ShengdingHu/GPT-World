# Automatic Environment Creation Utility

This is an Chain-of-Thought Tool Learning implementation of automatic environment creation.

## Example Usage

Use `create.py` to generate a `environment.json` by specifying a prompt describing your request as follows.

```sh
python create.py "Create a fine grained neighborhood with 
an area of Japanese restaurant (with a cook, tables, chairs, foods), 
an area of Chinese restaurant (with a cook, tables, chairs, foods), 
an area of Turkish restaurant (with a cook, tables, chairs, foods), 
an area of Starbucks (coffee machine, coffee staff), 
an area of 711 shop (stocks, drinks, snacks, etc), 
a grass area (with flower, people, pets, etc), 
an area of Alice's house (includes some furniture, like sofa, bed, bookshelf, cooker, a yard with two apple trees, Alice is at home) 
an area of Bob's house (Bob is at home)
Each area could be assigned as a subtask.
Add policeman.
Add some animals and plants, vehicles, bikes, and pedestrains. 
"
```

The agent will create your environment with varying scales: from large areas to small objects. Example Outputs:

```
Thought: Thought: Okay, let's start with the neighborhood area.
Action: add_area
Action Input: {"name": "Neighborhood", "area_boundary": [0, 0, 200, 150]}
Action: add_area
Action Input: {"name": "Neighborhood", "area_boundary": [0, 0, 200, 150]}
Observation: Added area Neighborhood

Thought: Now, let's create the Chinese restaurant area.
Action: create_sub_task
Action Input: {"task": "Build a Chinese restaurant with a cook, tables, chairs, and delicious foods. The area should be about 30x30 and located in the center of the neighborhood.", "action_boundary": [70, 60, 100, 90]}
Action: create_sub_task
Action Input: {"task": "Build a Chinese restaurant with a cook, tables, chairs, and delicious foods. The area should be about 30x30 and located in the center of the neighborhood.", "action_boundary": [70, 60, 100, 90]}
Thought: Thought: Okay, let's start with adding the area for the Chinese restaurant.
Action: add_area
Action Input: {"name": "Chinese Restaurant", "area_boundary": [50, 45, 80, 75]}
Action: add_area
Action Input: {"name": "Chinese Restaurant", "area_boundary": [50, 45, 80, 75]}
Observation: Added area Chinese Restaurant

Thought: Now I need to add the objects in the restaurant. Let's start with the tables and chairs.
Action: add_object
Action Input: {"name": "Table 1", "location": [55, 50], "engine": "environment", "memory": ["This is a table in the restaurant"]}
Action: add_object
Action Input: {"name": "Table 1", "location": [55, 50], "engine": "environment", "memory": ["This is a table in the restaurant"]}
Observation: Added object Table 1

Thought: Let's add more tables and chairs to the restaurant.
Action: add_object
Action Input: {"name": "Table 2", "location": [55, 60], "engine": "environment", "memory": ["This is a table in the restaurant"]}
Action: add_object
Action Input: {"name": "Table 2", "location": [55, 60], "engine": "environment", "memory": ["This is a table in the restaurant"]}
Observation: Added object Table 2

Thought: I need to add the chairs now. 
Action: add_object
Action Input: {"name": "Chair 1", "location": [50, 52], "engine": "environment", "memory": ["This is a chair in the restaurant"]}
Action: add_object
Action Input: {"name": "Chair 1", "location": [50, 52], "engine": "environment", "memory": ["This is a chair in the restaurant"]}
Observation: Added object Chair 1

...

Thought: I think I have finished the given task.
Action: submit_job
Action Input: {}
Action: submit_job
Action Input: {}
Observation: Submitted job

Task finished!
Observation: Subtask finished.

...

Thought: Now, let's create the coffee bar area.
Action: create_sub_task
Action Input: {"task": "Build a coffee bar with a coffee machine and coffee staff. The area should be about 20x20 and located in the north of the neighborhood.", "action_boundary": [0, 60, 20, 80]}
Action: create_sub_task
Action Input: {"task": "Build a coffee bar with a coffee machine and coffee staff. The area should be about 20x20 and located in the north of the neighborhood.", "action_boundary": [0, 60, 20, 80]}
Thought: Thought: First, I need to add the coffee bar area to the environment.
Action: add_area
Action Input: {"name": "Coffee Bar", "area_boundary": [0, 30, 20, 50]}
Action: add_area
Action Input: {"name": "Coffee Bar", "area_boundary": [0, 30, 20, 50]}
Observation: Added area Coffee Bar

Thought: Next, I need to add the coffee machine to the coffee bar.
Action: add_object
Action Input: {"name": "Coffee Machine", "location": [5, 40], "engine": "object", "memory": ["I am a coffee machine", "I can make various types of coffee"]}
Action: add_object
Action Input: {"name": "Coffee Machine", "location": [5, 40], "engine": "object", "memory": ["I am a coffee machine", "I can make various types of coffee"]}
Observation: Added object Coffee Machine
...

```

After the program terminates, you will find an `outputs` folder.


## Finish

Then you have your own environment. Copy `outputs` folder to `world_instances` folder, rename it as `newenv` and run it by

```sh
python gptworld/run.py -W newenv
```

