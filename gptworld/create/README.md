# Automatic Environment Creation Utility

This is an Chain-of-Thought Tool Learning implementation of automatic environment creation utility.

## Example Use

```sh
python main.py 'Create a neighborhood with some Chinese restaurants (with a cook, tables, chairs, delicious foods), and coffee bar (coffee machine, coffee staff), 711 shop (stocks, drinks, snacks, etc), trees, grass area (with flower, old people, etc), roads (with some cars, bikes), multiple houses (includes some furniture, like sofa, bed, bookshelf, cooker, etc), all above should be areas, each task could be a subtask, assign the jobs with lots of details, no overlapping areas. Add some people and animals and plants, evenly distributed. Expect more unexpcted details.'
```

## Example Output

```
Thought: Thought: First, I need to create an area for the Raven Slaughterhouse.
Action: add_area
Action Input: {"name": "Raven Slaughterhouse", "area_boundary": [100, 200, 600, 800]}
Action: add_area
Action Input: {"name": "Raven Slaughterhouse", "area_boundary": [100, 200, 600, 800]}
Observation: Added area Raven Slaughterhouse

Thought: Next, I need to add some objects to the Raven Slaughterhouse area.
Action: add_object
Action Input: {"name": "Weapon Rack", "location": [150, 250], "engine": "environment", "memory": ["Contains various types of weapons"]}
Action: add_object
Action Input: {"name": "Weapon Rack", "location": [150, 250], "engine": "environment", "memory": ["Contains various types of weapons"]}
Observation: Added object Weapon Rack

Thought: I want to add some more objects to the Raven Slaughterhouse area, but I think it would be better to create subtasks for my assistant to help me with the finer details.
Action: create_sub_task
Action Input: {"task": "Create the torture chamber with chains and hooks", "action_boundary": [200, 300, 400, 500]}
Action: create_sub_task
Action Input: {"task": "Create the torture chamber with chains and hooks", "action_boundary": [200, 300, 400, 500]}
Thought: Thought: Okay, let's start with adding an area for the torture chamber.
Action: add_area
Action Input: {"name": "Torture Chamber", "area_boundary": [250, 350, 380, 480]}
Action: add_area
Action Input: {"name": "Torture Chamber", "area_boundary": [250, 350, 380, 480]}
Observation: Added area Torture Chamber

Thought: Now, I need to add the chains and hooks to the torture chamber. I will add them as objects.
Action: add_object
Action Input: {"name": "Chains", "location": [280, 380], "engine": "environment", "memory": ["Used for restraining prisoners"]}
Action: add_object
Action Input: {"name": "Chains", "location": [280, 380], "engine": "environment", "memory": ["Used for restraining prisoners"]}
Observation: Added object Chains

Thought: Next, I will add the hooks to the torture chamber.
Action: add_object
Action Input: {"name": "Hooks", "location": [310, 390], "engine": "environment", "memory": ["Used for hanging prisoners"]}
Action: add_object
Action Input: {"name": "Hooks", "location": [310, 390], "engine": "environment", "memory": ["Used for hanging prisoners"]}
Observation: Added object Hooks

Thought: Now, I need to add an agent, a torturer, to the torture chamber.
Action: add_agent
Action Input: {"name": "Torturer", "location": [270, 420], "memory": ["I am a professional torturer", "I work for the king", "I have been doing this for 20 years"]}
Action: add_agent
Action Input: {"name": "Torturer", "location": [270, 420], "memory": ["I am a professional torturer", "I work for the king", "I have been doing this for 20 years"]}
Observation: Added agent Torturer

Thought: I think I have finished the task. I will submit it now.
Action: submit_job
Action Input: {}
Action: submit_job
Action Input: {}
Observation: Submitted job

Task finished!
Observation: Subtask finished.

Thought: Now I can continue adding objects to the Raven Slaughterhouse area.
Action: add_object
Action Input: {"name": "Dead Body", "location": [300, 350], "engine": "environment", "memory": ["A victim of the Raven Slaughterhouse"] }
Action: add_object
Action Input: {"name": "Dead Body", "location": [300, 350], "engine": "environment", "memory": ["A victim of the Raven Slaughterhouse"] }
Observation: Added object Dead Body

Thought: I think I need to add some agents to the Raven Slaughterhouse area to make it more dangerous.
Action: add_agent
Action Input: {"name": "Gangster 1", "location": [200, 400], "memory": ["A member of the Raven Slaughterhouse"] }
Action: add_agent
Action Input: {"name": "Gangster 1", "location": [200, 400], "memory": ["A member of the Raven Slaughterhouse"] }
Observation: Added agent Gangster 1

Thought: I want to add more agents to the Raven Slaughterhouse area, but I think I should create another subtask for my assistant to help me create a gangster hideout.
Action: create_sub_task
Action Input: {"task": "Create the gangster hideout with a secret entrance and exit", "action_boundary": [300, 200, 500, 400]}
Action: create_sub_task
Action Input: {"task": "Create the gangster hideout with a secret entrance and exit", "action_boundary": [300, 200, 500, 400]}
Thought: Thought: Okay, first I need to create an area for the gangster hideout within the given boundary.
Action: add_area
Action Input: {"name": "Gangster Hideout", "area_boundary": [350, 250, 450, 350]}
Action: add_area
Action Input: {"name": "Gangster Hideout", "area_boundary": [350, 250, 450, 350]}
Observation: Added area Gangster Hideout

Thought: Now I need to add a secret entrance and exit to the hideout. I'll add two objects for that.
Action: add_object
Action Input: {"name": "Secret Entrance", "location": [350, 250], "engine": "object", "memory": ["This is a secret entrance", "Only gang members know about it"]}
Action: add_object
Action Input: {"name": "Secret Entrance", "location": [350, 250], "engine": "object", "memory": ["This is a secret entrance", "Only gang members know about it"]}
Observation: Added object Secret Entrance

Thought: Now I need to add the exit. I'll place it at a different location within the hideout.
Action: add_object
Action Input: {"name": "Secret Exit", "location": [450, 350], "engine": "object", "memory": ["This is a secret exit", "Only gang members know about it"]}
Action: add_object
Action Input: {"name": "Secret Exit", "location": [450, 350], "engine": "object", "memory": ["This is a secret exit", "Only gang members know about it"]}
Observation: Added object Secret Exit

Thought: Now I need to add some gang members to the hideout.
Action: add_agent
Action Input: {"name": "Gang Member 1", "location": [375, 275], "memory": ["I am a member of the gang", "I know about the secret entrance and exit"]}
Action: add_agent
Action Input: {"name": "Gang Member 1", "location": [375, 275], "memory": ["I am a member of the gang", "I know about the secret entrance and exit"]}
Observation: Added agent Gang Member 1

Thought: I think I need to add more gang members to make the hideout more realistic.
Action: add_agent
Action Input: {"name": "Gang Member 2", "location": [400, 300], "memory": ["I am a member of the gang", "I know about the secret entrance and exit"]}
Action: add_agent
Action Input: {"name": "Gang Member 2", "location": [400, 300], "memory": ["I am a member of the gang", "I know about the secret entrance and exit"]}
Observation: Added agent Gang Member 2

Thought: I think I have finished the given task.
Action: submit_job
Action Input: {}
Action: submit_job
Action Input: {}
Observation: Submitted job

Task finished!
Observation: Subtask finished.

Thought: I think I have finished the given task.
Action: submit_job
Action Input: {}
Action: submit_job
Action Input: {}
Observation: Submitted job

Task finished!
```