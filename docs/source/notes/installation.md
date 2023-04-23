
(installation)=


## Installation

```bash
python setup.py develop
```
or
```bash
python setup.py install
```


## Check your connectivity with the model engine.

```bash
python -c "from gptworld.models.openai import chat; print(chat('Hello'))"
python -c "from gptworld.models.openai import get_embedding; print(get_embedding('Hello'))"
```
If it prints `Hello! How may I assist you today?`, it is connected!


## Check your local environment for the web demo.
We use Vue + TypeScipt + Phaser3 as the frontend, and use a simple flask app as
 the backend. So if you want to run smoothly, you may want to install them first.


```bash
pip install Flask
pip install Flask_CORS
cd game/text_grid
npm install
npm install phaser
```

To check they are correctly installed, do the following：
1. 
```bash
cd game/text_grid
python app.py
```
2. 
```bash
cd game/text_grid/frontend
npm run dev
```
This will give a port (default: http://localhost:5173), view it in your browser.



# Config your json file

convention list:

- The name and id should be unique for each agent, object, envs
  


