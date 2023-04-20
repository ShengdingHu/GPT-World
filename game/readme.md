# Visualization Your GPTWorld in Browser!

## Setup

essentially, in your command line

```bash
pip install Flask
pip install Flask_CORS
cd text_grid
npm install
npm install phaser
```

## Run demo independently

 (without the main loop of the GPTWorld)

1. at game/text_grid
```bash
python app.py
```

2. open another termial
```bash
cd game/text_grid/frontend
npm run dev
```

3. view demo in your browser.


## FYI

1. If you have any question, refer to [this blog](https://saricden.com/how-to-setup-a-phaser-3-project-with-vite)


2. Phaser 3 API doc refer to [this doc](https://photonstorm.github.io/phaser3-docs/)

3. Develop manual
    - [Add obstacles](https://developer.amazon.com/blogs/post/Tx3AT4I2ENBOI6R/Intro-to-Phaser-Part-3-Obstacles-Collision-Score-Sound-and-Publishing)
