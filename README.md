# 🌎GPTWorld: an experimental multi-agent sandbox world.


🌎GPTWorld is an experimental multi-agent sandbox world. 🔬 Unlike typical sandbox games, interactions in GPTWorld are not fully defined by pre-written scripts 📜 and rules, but rather **inferred by a world engine based on large models 🤖.**. In this world, virtual agents and objects are equipped with long term memory, they can act, react, and communicate with each other, all supported by AI 🤯. 

The creation of a sandbox world is often considered to require advanced game development techniques that are beyond the reach of most individuals. This is where 🌎GPTWorld comes to the rescue! 🛠️ Our goal is to make the process of creating a diverse range of sandboxes more accessible by enabling players to construct custom worlds using simple configuration files or even natural language 🤩.

Through this easy-to-use **world creation** feature, we hope to inspire everyone to construct their own unique worlds. As a result, a vibrant sandbox environment will emerge, allowing intelligent agents to explore various creations through community sharing 🤝.

👨‍💻👩‍💻 Join us on this exciting journey of creating a groundbreaking sandbox world with limitless possibilities 🚀!

## Project Status
### 1. Currently, 🌍GPTWorld supports:

👨‍💻 Easily creating your environment and entities using JSON and mounting them onto your world
🏃 Starting the environment's autonomous operation with just one command
👀 Observing the behavior of the agent in your web browser

### 2. Experimental feature
🗣️ Creating environments with natural languages

### 3. TODOS!
🤝 Allowing players to build and share environments in a distributed way



<br/>

## Usage

### Install

It is suggested to use `python=3.8` on all platforms.

1. Download project by

```sh
git clone https://github.com/ShengdingHu/GPT-World.git
```

or download zip file and unzip it.

2. (Optional) Create a python virtual enviornment by 

```
conda create -n gptworld python=3.8
```
* Note that python3.8 support websockiet the best, other python versions may encounter issues in web display currently. *

3. Go to project directory by 

```
cd GPT-World
```

4. Install dependencies by

```sh
pip install -r requirements.txt
```

5. Then install this library by

```sh
pip install .
```

6. Build the front end
```sh
cd io/frontend_new/rpg-game/
npm run build
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


## 🙏Acknowledgements

 This project was greatly inspired by [*Generative Agents: Interactive Simulacra of Human Behavior*](https://arxiv.org/abs/2304.03442)  during development, where the mechanism of agents' behavior takes the reflection-summary-plan framework.

## 🚨 Disclaimer:
This project is for academic and experimental purposes only. We currently suspect that it is far from a usable game product.


## Star History

<br>
<div align="center">

<img src="https://api.star-history.com/svg?repos=THUNLP/GPTWorld&type=Date" width="600px">

</div>
<br>

## Contributor

<a href = "https://github.com/ShengdingHu/GPT-World/graphs/contributors">
  <img src = "https://contrib.rocks/image?repo = GitHub_username/repository_name"/>
</a>