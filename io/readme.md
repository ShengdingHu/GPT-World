# Visualize Your GPTWorld in Browser

We have designed a web interface for users to view and interact with a world instance. The backend server should be started by specifying a `world_instance`, after that, users (both the host and remote users) could use a url to access the web interface.

## Usage

1. Make sure you have install `requirements.txt` in project root directory.

2. Run backend server by

```bash
python app.py -W alice_home
```

3. View in your browser:

Go to `http://localhost:5001` to view your world, others could use `http://{Your IP address}:5001` to access.

4. Distribute the URL to others.

---

## Development

1. Make sure you have install `requirements.txt` in project root directory.

2. Install frontend development environment by

```bash
cd frontend_new/rpg-game
npm install
```

3. Change 

Go to `frontend_new/rpg-game` -> `src` -> `components` -> `Chat.js` and `GameArea.js`, change `API_ROOT` to `http://localhost:5001` for development mode.

Run backend server

```bash
python app.py --world_instance alice_home
```

Run frontend develop server: open another termial
```bash
cd frontend_new/rpg-game
npm run dev
```

View demo in your browser at `http://localhost:3000`

---

## GPT-World IO Module


