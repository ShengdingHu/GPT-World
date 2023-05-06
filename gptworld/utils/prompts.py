import json
import os
from gptworld.utils.logging import get_logger

logger = get_logger(__name__)

base_prompt = {
"subject_parsing": """What is the subject for the following sentence, i.e., the following sentence describes whom? Just give me the subject concisely. Sentence: {sentence}. Subject:""",

"reaction_prompt": """Now you are performing actions as an agent named {name} in a virtual world. Your mission to take the agent as yourself and directly provide what the agent will do based on the following information:
(1) The agent's description: {summary}
(2) Current time is {time}
(3) Your current status is {status}
(4) Some incoming observation is {observation}
(5) Some background observation is {background_observation}. 
In terms of how you actually perform the action in the virtual world, you take action for the agent by calling functions. Currently, there are the following functions that can be called.

- act(description, target=None): do some action. `description` describes the action, set `description` to None for not act. `target` should be the concrete name, for example, Tim is a teacher, then set `target` to `Tim`, not `teacher`. 
- say(content, target=None): say something,`content` is the sentence that the agent will say.
- move(description): move to somewhere. `description` describes the movement, set description to None for not move .
- change_status(bool): whether to change the agent's current status, True for change, False for not change. 

Some actions may not be needed in this situation. Call one function at a time, please give a thought before calling these actions, i.e., use the following format strictly:
            
Thought: Since, ..., I might need to say something.
Action: say("hello", target="Alice")
Observation:
Thought: Since, ..., I don't need to do action.
Action: act(None)
Observation:
Thought: Since, ..., I don't need move to anywhere.
Action: move(None)
Observation:
Thought: I think the current status: sleeping  does not need to be changed.
Action: change_status(False)
Observation:
Thought: I think I've finished my action as the agent. 
Action: end()
Observation:

Now begin your actions as the agent. **Important: If a function has been called previously, it CANNOT be called anymore, instead, end() should be called.** """,

"broadcast_observations": """You are simulating an environment. When an action happens in your environment, you should paraphrase the action to (and only to) the potential receivers in your environment. Please judge whether you should broadcast the message when meets one of the following principles:
1. The message is meaningful to the potential receiver. broadcast a `say` action to an object without life (like desk) is not meaningful, while broadcast a `push` action to the desk is meaningful.
2. The message might be captured by the potential receiver because of physical distance althought the potential receiver is not the direct target. For example, A is saying some content to B, C is close to A and B, then C might also hear it. 
3. The message is related to the potential receiver. For example, a `read book` action is not related to the bed in any way, so you shouldn't broadcast. 

Also follow the following rules:
1. Only broadcast to the listed potential receivers, do not imagine not existing ones. 

You should broadcast using the following format (end with `Finish_Broadcast` ):
Thought: I will look through the list and pick the ones that meets one of the following principles. I think ... are related, ... will get information, ... might capter.
Broadcast:
1. To A: some content
2. To B: some content
...
N. To N: some content
Finish_Broadcast

Now, in your environment, there are the following potential receivers: {agents_and_objects}, please broadcast the following action: ```{name} -> {targets} : {content}``` to the potential receivers. )
"""

}


def load_prompt(file_dir, file_name="prompts.json", key=None):
    prompt_path = os.path.join(file_dir, file_name)
    if os.path.exists(prompt_path):
        with open(os.path.join(file_dir, file_name), 'r') as fin:
            data = json.load(fin)
            prompt = data.get(key, '')
    else:
        prompt = ''

    if prompt == '':
        prompt = base_prompt.get(key, '')

    if prompt == '':
        logger.warning(f"No prompt of {key} has been found")
    return prompt
        


