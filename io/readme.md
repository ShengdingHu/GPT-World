# Visualization Your GPTWorld in Browser!

## Normal User Setup

Install requirements.txt in the parent directory:

```bash
cd ..
pip install -r requirements.txt
```

Run backend server (with pre-compiled frontend inside):

```bash
python app.py --world_instance alice_home
```

View in your browser:

Go to `http://localhost:5001` to view your world, others could use `http://{Your IP address}:5001` to access.

---

## Developer Setup

Install requirements.txt in the parent directory

```bash
cd ..
pip install -r requirements.txt
```

Install frontend development environment

```bash
cd frontend
npm install
npm install phaser
```

Run backend server

```bash
python app.py --world_instance alice_home
```

Run frontend develop server: open another termial
```bash
cd frontend
npm run dev
```

View demo in your browser at `http://localhost:5173`

---

## FYI

1. If you have any question, refer to [this blog](https://saricden.com/how-to-setup-a-phaser-3-project-with-vite)

2. Phaser 3 API doc refer to [this doc](https://photonstorm.github.io/phaser3-docs/)

3. Develop manual
    - [Add obstacles](https://developer.amazon.com/blogs/post/Tx3AT4I2ENBOI6R/Intro-to-Phaser-Part-3-Obstacles-Collision-Score-Sound-and-Publishing)
