# Visualize Your GPTWorld Instance in Browser

We have designed a web interface for users to view and interact with a world instance. The server should be started by specifying a `world_instance`, after that, users (including remote users) could use a url to access the web interface.

## Usage

1. Make sure you have install `requirements.txt` in project root directory.

2. Start server by

```bash
python app.py -W alice_home
```

The server will try to read `world_instance` folder in project root directory and find your specified world instance.

3. View in your browser:

Go to `http://localhost:5001` to view your world, others could use `http://{Your IP address}:5001` to access.

4. Distribute the URL to others.

---

## For Developer

The web interface consists of two components: a `react` frontend and a `flask` backend. In release version, we have pre-compiled the frontend client, and make it a part of backend, which will make all things convenient. 

For develooment, we should seperately handle frontend and backend.

1. Make sure you have install `requirements.txt` in project root directory.

2. Install frontend development environment by

```bash
cd frontend_new/rpg-game
npm install
```

3. Start backend server by 

```bash
cd .
python app.py -W alice_home
```

4. Start frontend development server by

```bash
cd frontend_new/rpg-game
npm start
```

5. View

View demo in your browser at `http://localhost:3000`

6. Release

If you would like to release your work, please pre-compile your frontend client by

```bash
cd frontend_new/rpg-game
npm run build
```

It will produce a `build` folder under `frontend_new/rpg-game`. Then you are done, the backend server will automatically read it.