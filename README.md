# 🌎GPTWorld: an experimental multi-agent sandbox world.


🌎GPTWorld is an experimental multi-agent sandbox world. 🔬 Unlike typical sandbox games, interactions in GPTWorld are not defined by pre-written scripts 📜, but rather **inferred by a world engine based on large models 🤖.**. In this world, virtual agents and objects are equipped with long term memory and short term memory, they can act, react, and communicate with each other, all supported by AI 🤯. 

🛠️ To facilitate the creation of a more diverse range of sandboxes, we aim to allow players to create custom worlds through simple configuration files or even natural language 🤩, and look forward to building a rich sandbox world for intelligent agents to explore through community sharing 🤝.

👨‍💻👩‍💻 Join us on this exciting journey of creating a groundbreaking sandbox world with limitless possibilities 🚀!


**Currently, 🌍GPTWorld supports:**

👨‍💻 Easily creating your environment and entities using JSON and mounting them onto your world
🏃 Starting the environment's autonomous operation with just one command
👀 Observing the behavior of the agent in your web browser

🎉 **Coming soon:**
🤝 Allowing players to build and share environments in a distributed way
🗣️ Creating environments with natural languages

🙏**Acknowledgements:** This project was greatly inspired by [*Generative Agents: Interactive Simulacra of Human Behavior*](https://arxiv.org/abs/2304.03442)  during development, where the mechanism of agents' behavior takes the reflection-summary-plan framework.

🚨 **Disclaimer:**
This project is for academic and experimental purposes only. We currently suspect that it is far from a usable game product.


<br/>

## Usage

### Install

Download this library by

```sh
git clone https://github.com/ShengdingHu/GPT-World.git
```

or download zip file.

Then go to library directory.

It is suggested to use `python=3.8` on all platforms.


(Optional) Create a python3.8 enviornment by

```
conda create -n gptworld python=3.8
```

Install dependencies by

```sh
pip install -r requirements.txt
```

Then install this library by

```sh
pip install .
```

### Run examples
We currently provide some example sandboxes in  `world_instances/`, choose one that you want to launch.
Take `alice_home` as an example.

1. start the world engine
```
python gptworld/run.py -W alice_home
```

2. start the web server
```
python io/app.py -W alice_home
```
now open the 5001 port of your localhost, and you will be able to see a simple environment.

### (🧪Experimental) Create your own
1. If you want to create your world instance,
modify the requirement in `gptworld/create_world.py` and run
```
python gptworld/create_world.py 
```

## Global Configs
```bash
export GPTWORLD_LOG_LEVEL=XXX # (XXX can be debug, info, warning ...) to set the logging level
```
