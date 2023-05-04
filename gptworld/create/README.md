# Automatic Environment Creation Utility

This is an Chain-of-Thought Tool Learning implementation of automatic environment creation.

## First step: Generate `environment.json`

Firstly, use `main.py` to generate a `environment.json` by specifying a prompt describing your request as follows.

```sh
python main.py "Create a neighborhood with some Chinese restaurants (with a cook, tables, chairs, delicious foods), and coffee bar (coffee machine, coffee staff), 711 shop (stocks, drinks, snacks, etc), trees, grass area (with flower, old people, etc), roads (with some cars, bikes), Alice's house and Bob's house (includes some furniture, like sofa, bed, bookshelf, cooker, and their families, a yard with two apple trees, etc), all above should be areas, each task could be a subtask, assign the jobs with lots of details, no overlapping areas. Add some people and animals and plants, evenly distributed. Expect more details. Areas should not overlap with each other."
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

[WARNING|gptworld.models.openai_api:35] 2023-05-04 03:28:32 >> Unable to generate response
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

Thought: Let's add more chairs to the restaurant.
Action: add_object
Action Input: {"name": "Chair 2", "location": [50, 58], "engine": "environment", "memory": ["This is a chair in the restaurant"]}
Action: add_object
Action Input: {"name": "Chair 2", "location": [50, 58], "engine": "environment", "memory": ["This is a chair in the restaurant"]}
Observation: Added object Chair 2

Thought: Now it's time to add the cook and the delicious foods to the restaurant.
Action: add_agent
Action Input: {"name": "Cook", "location": [65, 65], "memory": ["I am a cook in the Chinese Restaurant"]}
Action: add_agent
Action Input: {"name": "Cook", "location": [65, 65], "memory": ["I am a cook in the Chinese Restaurant"]}
Observation: Added agent Cook

Thought: I need to add the delicious foods to the restaurant. 
Action: add_object
Action Input: {"name": "Dumplings", "location": [60, 55], "engine": "object", "memory": ["I am a delicious dumpling in the Chinese Restaurant", "I am made by the Cook"]}
Action: add_object
Action Input: {"name": "Dumplings", "location": [60, 55], "engine": "object", "memory": ["I am a delicious dumpling in the Chinese Restaurant", "I am made by the Cook"]}
Observation: Added object Dumplings

[WARNING|gptworld.models.openai_api:35] 2023-05-04 03:28:47 >> Unable to generate response
Thought: I think I have finished the given task.
Action: submit_job
Action Input: {}
Action: submit_job
Action Input: {}
Observation: Submitted job

Task finished!
Observation: Subtask finished.

Thought: Now, let's add the Chinese restaurant area.
Action: add_area
Action Input: {"name": "Chinese Restaurant", "area_boundary": [70, 60, 100, 90]}
Action: add_area
Action Input: {"name": "Chinese Restaurant", "area_boundary": [70, 60, 100, 90]}
Observation: Added area Chinese Restaurant

Thought: Let's add the necessary objects and agents to the Chinese restaurant area.
Action: add_object
Action Input: {"name": "Cook", "location": [80, 70], "engine": "object", "memory": ["I am the cook of this restaurant", "I can cook delicious Chinese food"]}
Action: add_object
Action Input: {"name": "Cook", "location": [80, 70], "engine": "object", "memory": ["I am the cook of this restaurant", "I can cook delicious Chinese food"]}
Observation: Added object Cook

Thought: Let's add tables and chairs to the Chinese restaurant area.
Action: add_object
Action Input: {"name": "Table 1", "location": [75, 65], "engine": "environment", "memory": ["This is a table in the Chinese restaurant"]}
Action: add_object
Action Input: {"name": "Table 1", "location": [75, 65], "engine": "environment", "memory": ["This is a table in the Chinese restaurant"]}
Observation: Added object Table 1

Thought: Let's add more tables and chairs to the Chinese restaurant area.
Action: add_object
Action Input: {"name": "Table 2", "location": [75, 80], "engine": "environment", "memory": ["This is a table in the Chinese restaurant"]}
Action: add_object
Action Input: {"name": "Table 2", "location": [75, 80], "engine": "environment", "memory": ["This is a table in the Chinese restaurant"]}
Observation: Added object Table 2

[WARNING|gptworld.models.openai_api:35] 2023-05-04 03:29:00 >> Unable to generate response
Thought: Let's add some delicious foods to the Chinese restaurant area.
Action: add_object
Action Input: {"name": "Dumplings", "location": [85, 75], "engine": "environment", "memory": ["This is a plate of delicious dumplings in the Chinese restaurant"]}
Action: add_object
Action Input: {"name": "Dumplings", "location": [85, 75], "engine": "environment", "memory": ["This is a plate of delicious dumplings in the Chinese restaurant"]}
Observation: Added object Dumplings

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

Thought: Now I need to add coffee staff to the coffee bar.
Action: add_agent
Action Input: {"name": "Coffee Staff", "location": [10, 35], "memory": ["I am a barista", "I can make great coffee", "I am friendly and welcoming"]}
Action: add_agent
Action Input: {"name": "Coffee Staff", "location": [10, 35], "memory": ["I am a barista", "I can make great coffee", "I am friendly and welcoming"]}
Observation: Added agent Coffee Staff

Thought: I think I have finished the given task.
Action: submit_job
Action Input: {}
Action: submit_job
Action Input: {}
Observation: Submitted job

Task finished!
Observation: Subtask finished.

Thought: Let's add the coffee bar area.
Action: add_area
Action Input: {"name": "Coffee Bar", "area_boundary": [0, 60, 20, 80]}
Action: add_area
Action Input: {"name": "Coffee Bar", "area_boundary": [0, 60, 20, 80]}
Observation: Added area Coffee Bar

Thought: Now, let's add the necessary objects and agents to the coffee bar area.
Action: add_object
Action Input: {"name": "Coffee Machine", "location": [5, 70], "engine": "object", "memory": ["I am the coffee machine in this coffee bar", "I can make different types of coffee"]}
Action: add_object
Action Input: {"name": "Coffee Machine", "location": [5, 70], "engine": "object", "memory": ["I am the coffee machine in this coffee bar", "I can make different types of coffee"]}
Observation: Added object Coffee Machine

Thought: Let's add a coffee staff to the coffee bar area.
Action: add_agent
Action Input: {"name": "Coffee Staff", "location": [10, 75], "memory": ["I work at this coffee bar", "I can make delicious coffee for customers"]}
Action: add_agent
Action Input: {"name": "Coffee Staff", "location": [10, 75], "memory": ["I work at this coffee bar", "I can make delicious coffee for customers"]}
Observation: Added agent Coffee Staff

Thought: Now, let's create the 711 shop area.
Action: create_sub_task
Action Input: {"task": "Build a 711 shop with stocks, drinks, and snacks. The area should be about 25x25 and located in the south of the neighborhood.", "action_boundary": [175, 60, 200, 85]}
Action: create_sub_task
Action Input: {"task": "Build a 711 shop with stocks, drinks, and snacks. The area should be about 25x25 and located in the south of the neighborhood.", "action_boundary": [175, 60, 200, 85]}
Thought: Thought: First, I need to add the area of the 711 shop.
Action: add_area
Action Input: {"name": "711 Shop", "area_boundary": [175, 60, 200, 85]}
Action: add_area
Action Input: {"name": "711 Shop", "area_boundary": [175, 60, 200, 85]}
Observation: Added area 711 Shop

Thought: Now, I need to add the objects to the 711 shop. I will start with stocks.
Action: add_object
Action Input: {"name": "Stocks", "location": [180, 65], "engine": "environment", "memory": ["I am a shelf of stocks", "I contain various products", "I need to be restocked regularly"]}
Action: add_object
Action Input: {"name": "Stocks", "location": [180, 65], "engine": "environment", "memory": ["I am a shelf of stocks", "I contain various products", "I need to be restocked regularly"]}
Observation: Added object Stocks

Thought: Next, I will add drinks to the 711 shop.
Action: add_object
Action Input: {"name": "Drinks", "location": [185, 70], "engine": "environment", "memory": ["I am a fridge of drinks", "I contain various beverages", "I need to be restocked regularly"]}
Action: add_object
Action Input: {"name": "Drinks", "location": [185, 70], "engine": "environment", "memory": ["I am a fridge of drinks", "I contain various beverages", "I need to be restocked regularly"]}
Observation: Added object Drinks

Thought: Lastly, I will add snacks to the 711 shop.
Action: add_object
Action Input: {"name": "Snacks", "location": [190, 75], "engine": "environment", "memory": ["I am a shelf of snacks", "I contain various snacks", "I need to be restocked regularly"]}
Action: add_object
Action Input: {"name": "Snacks", "location": [190, 75], "engine": "environment", "memory": ["I am a shelf of snacks", "I contain various snacks", "I need to be restocked regularly"]}
Observation: Added object Snacks

Thought: Now, I need to add an agent to the 711 shop. Let's add a shopkeeper named John.
Action: add_agent
Action Input: {"name": "John", "location": [195, 80], "memory": ["I am the shopkeeper of this 711 shop", "I need to manage the stocks, drinks, and snacks", "I need to provide good service to customers"]}
Action: add_agent
Action Input: {"name": "John", "location": [195, 80], "memory": ["I am the shopkeeper of this 711 shop", "I need to manage the stocks, drinks, and snacks", "I need to provide good service to customers"]}
Observation: Added agent John

[WARNING|gptworld.models.openai_api:35] 2023-05-04 03:29:36 >> Unable to generate response
Thought: I think I have finished the given task.
Action: submit_job
Action Input: {}
Action: submit_job
Action Input: {}
Observation: Submitted job

Task finished!
Observation: Subtask finished.

Thought: Let's add the 711 shop area.
Action: add_area
Action Input: {"name": "711 Shop", "area_boundary": [175, 60, 200, 85]}
Action: add_area
Action Input: {"name": "711 Shop", "area_boundary": [175, 60, 200, 85]}
Observation: Added area 711 Shop

Thought: Now, let's add the necessary objects to the 711 shop area.
Action: add_object
Action Input: {"name": "Stocks", "location": [180, 70], "engine": "environment", "memory": ["This is a shelf with various stocks in the 711 shop"]}
Action: add_object
Action Input: {"name": "Stocks", "location": [180, 70], "engine": "environment", "memory": ["This is a shelf with various stocks in the 711 shop"]}
Observation: Added object Stocks

Thought: Let's add drinks to the 711 shop area.
Action: add_object
Action Input: {"name": "Coca Cola", "location": [185, 75], "engine": "environment", "memory": ["This is a bottle of Coca Cola in the 711 shop"]}
Action: add_object
Action Input: {"name": "Coca Cola", "location": [185, 75], "engine": "environment", "memory": ["This is a bottle of Coca Cola in the 711 shop"]}
Observation: Added object Coca Cola

Thought: Let's add some snacks to the 711 shop area.
Action: add_object
Action Input: {"name": "Potato Chips", "location": [190, 80], "engine": "environment", "memory": ["This is a packet of potato chips in the 711 shop"]}
Action: add_object
Action Input: {"name": "Potato Chips", "location": [190, 80], "engine": "environment", "memory": ["This is a packet of potato chips in the 711 shop"]}
Observation: Added object Potato Chips

Thought: Now, let's create the trees and grass area.
Action: create_sub_task
Action Input: {"task": "Create a green area with trees, grass, flowers, and some old people. The area should be about 50x50 and located in the west of the neighborhood.", "action_boundary": [50, 0, 100, 50]}
Action: create_sub_task
Action Input: {"task": "Create a green area with trees, grass, flowers, and some old people. The area should be about 50x50 and located in the west of the neighborhood.", "action_boundary": [50, 0, 100, 50]}
Thought: Thought: Okay, let's start by adding an area for the green space.
Action: add_area
Action Input: {"name": "Green Area", "area_boundary": [0, 0, 50, 50]}
Action: add_area
Action Input: {"name": "Green Area", "area_boundary": [0, 0, 50, 50]}
Observation: Added area Green Area

Thought: Now let's add some trees, grass, and flowers to the green area.
Action: add_object
Action Input: {"name": "Tree", "location": [10, 10], "engine": "environment", "memory": ["I am a tree", "I provide shade and oxygen"]}
Action: add_object
Action Input: {"name": "Tree", "location": [10, 10], "engine": "environment", "memory": ["I am a tree", "I provide shade and oxygen"]}
Observation: Added object Tree

Thought: Let's add more trees and some grass and flowers around them.
Action: add_object
Action Input: {"name": "Tree", "location": [20, 20], "engine": "environment", "memory": ["I am a tree", "I provide shade and oxygen"]}
Action: add_object
Action Input: {"name": "Tree", "location": [20, 20], "engine": "environment", "memory": ["I am a tree", "I provide shade and oxygen"]}
Observation: Added object Tree

Thought: Let's add some grass to the green area.
Action: add_object
Action Input: {"name": "Grass", "location": [30, 30], "engine": "environment", "memory": ["I am grass", "I am soft and green"]}
Action: add_object
Action Input: {"name": "Grass", "location": [30, 30], "engine": "environment", "memory": ["I am grass", "I am soft and green"]}
Observation: Added object Grass

Thought: Let's add some flowers to the green area.
Action: add_object
Action Input: {"name": "Flower", "location": [40, 40], "engine": "environment", "memory": ["I am a flower", "I am colorful and beautiful"]}
Action: add_object
Action Input: {"name": "Flower", "location": [40, 40], "engine": "environment", "memory": ["I am a flower", "I am colorful and beautiful"]}
Observation: Added object Flower

Thought: Now let's add some old people to the green area.
Action: add_agent
Action Input: {"name": "Old Man", "location": [15, 15], "memory": ["I am an old man", "I like to sit and enjoy nature"]}
Action: add_agent
Action Input: {"name": "Old Man", "location": [15, 15], "memory": ["I am an old man", "I like to sit and enjoy nature"]}
Observation: Added agent Old Man

Thought: I think the green area is complete, let's submit the job.
Action: submit_job
Action Input: {}
Action: submit_job
Action Input: {}
Observation: Submitted job

Task finished!
Observation: Subtask finished.

Thought: Let's add the trees and grass area.
Action: add_area
Action Input: {"name": "Green Area", "area_boundary": [50, 0, 100, 50]}
Action: add_area
Action Input: {"name": "Green Area", "area_boundary": [50, 0, 100, 50]}
Observation: Added area Green Area

[WARNING|gptworld.models.openai_api:35] 2023-05-04 03:30:04 >> Unable to generate response
Thought: Let's add some trees to the green area.
Action: add_object
Action Input: {"name": "Tree 1", "location": [60, 10], "engine": "environment", "memory": ["This is a tree in the green area"]}
Action: add_object
Action Input: {"name": "Tree 1", "location": [60, 10], "engine": "environment", "memory": ["This is a tree in the green area"]}
Observation: Added object Tree 1

Thought: Let's add more trees to the green area.
Action: add_object
Action Input: {"name": "Tree 2", "location": [70, 20], "engine": "environment", "memory": ["This is a tree in the green area"]}
Action: add_object
Action Input: {"name": "Tree 2", "location": [70, 20], "engine": "environment", "memory": ["This is a tree in the green area"]}
Observation: Added object Tree 2
```

After the program terminates, you will find `environment.json` in `outputs` folder.

## Second step: 

Secondly, create embeddings for named entities in your environment for further visualization.

```
python create_embedding.py
```

After the program terminates, you will find a `embeddings.json` in `outputs` folder.

## Finish

Then you have your own environment. Copy `outputs` folder to `world_instances` folder and run it.

