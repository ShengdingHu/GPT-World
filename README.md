# GPT-World Server

一个基于GPT搭建的世界，世界中的主观个体和客观物体均由GPT来支持其行动。
世界由多个环境构成，使用者可以（1）轻松地创建自己的环境，以及其中的主体和客体并挂载到世界上，（2）创造自己的agent并让其能访问自己或其他的世界。

Server 是开源的、分布式的，每个人都可以 host 自己的服务器和朋友们分享。


## How to run

### 1. If you want to see the demo, please
cd to the  `game/` folder, do as the `game/readme.md` suggest. If you can view the demo in the localhost, you are done. 
If not, you might stuck at `npm install`, please install `npm`

```

### 2. run the main loop of the world
cd to the root directory of this project
```bash
python gptworld/run.py
```

## Development Contract

### Environment and Agent storage
at static_files/YOUR_ENV_NAME/




