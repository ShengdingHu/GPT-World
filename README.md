# 🌎GPTWorld: an experimental multi-agent sandbox world.


🌎GPTWorld is an experimental multi-agent sandbox world. 🔬 Unlike typical sandbox games, interactions in GPTWorld are not defined by pre-written scripts 📜, but rather **inferred by a world engine based on large models 🤖.** In this world, virtual agents and objects can act, react, interact, and communicate autonomously, all supported by AI 🤯.

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

🧪 **Disclaimer:**
This project is for academic and experimental purposes only. We currently suspect that it is far from a usable game product.


<br/>
<br/>
<br/>

# System Design


<img src="./images/mermaid-diagram-2023-04-29-031656.svg" style="width:50%;">

|Module Name|Directory|
|--|--|
|User Client|`./io/frontend/`|
|Backend|`./io/`|
|File Storage|`./static_files/`|
|Core Simulator|`./gptworld/core/`|
|Environment Generating Tool|`./environment_creation_tool/`|

