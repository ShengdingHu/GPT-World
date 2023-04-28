import './style.css';
import { Scene, Game, WEBGL, GameObjects} from 'phaser';
import Phaser from 'phaser';
import { io, Socket } from "socket.io-client";


const API_ROOT = "http://localhost:5001";

// the ratio betweem game height and width
const HEIGHT_WIDTH_RATIO = 3 / 4;

// I. UI Logging Implementation
const messagesElement = document.getElementById('messages')!;

// socket connection to backend server
const socket: Socket = io(API_ROOT);

// on connect with backend server
socket.on("connect", () => {
  console.log("Connected to the server");
});

// an active test message form backend server
socket.on("welcome", (event) => {
  console.log(event.message);
});

// normal messages from backend server
socket.on("server_message", (event) => {
  console.log("Received message:", event);
  
  const data = event.message as string[];
  data.forEach((messageData) => {
    const [sender, text] = messageData.split('|');
    const message = {
      sender,
      text,
      time: new Date(),
    };

    const colors = ['red', 'green', 'blue', 'orange', 'purple'];
    const randomIndex = Math.floor(Math.random() * colors.length);
    const randomColor = colors[randomIndex];
    const messageElement = document.createElement('div');
    messageElement.innerHTML = `<span style="font-weight: bold; color: ${randomColor}">${message.sender}</span>: ${message.text}`;
    messagesElement.appendChild(messageElement);
  });
});

socket.on("disconnect", () => {
  console.log("Disconnected from the server");
});

window.onbeforeunload = function() {
  // on reload
  return "Sure to reload?"
};


// II. Game Interface Implementation
const canvas = document.getElementById('game') as HTMLCanvasElement;
const ORIGIN_X = 100;
const ORIGIN_Y = 100;

class ObjectSprite extends Phaser.GameObjects.Sprite {
  // This class is applicable for all objects (not including areas), it extends the Sprite class to store more information we need

  // add an attribute to store the tooltip
  tooltip?: Phaser.GameObjects.Text; 

  // add an attribute to store the name displayed in the tooltip
  display_name?: string; 

  constructor(scene: Phaser.Scene, x: number, y: number, texture: string) {
    super(scene, x, y, texture);
  }
}

function showTooltip(sprite: ObjectSprite) {
  // once mouse is on a sprite, this function will be called
  if (sprite.tooltip) {
    // tooltip exists, nothing to do
  } else {
    let text = sprite.scene.add.text(
      sprite.x,
      sprite.y,
      sprite.display_name as string,
        {
          font: '15px Arial',
          color: '#000000',
          backgroundColor: '#ffffff',
          padding: 4 as Phaser.Types.GameObjects.Text.TextPadding,
        }
      );
    sprite.tooltip = text;
  }
}

function hideTooltip(sprite: ObjectSprite) {
  // once mouse leaves the sprite, this function will be called
  if (sprite.tooltip) {
    let text = sprite.tooltip;
    text.destroy();
    sprite.tooltip = undefined;
  } else {
    // if there is no tooltip displayed, do nothing
  }
}

function loadIcon(name: string, scene: Scene) {
  // given a sprite name, this function will fetch an icon from backend and store it in Phaser scene, this function is non-blocking, so the icon of sprites will be updated later
  let url = API_ROOT + "/text_to_icon?name="+name;
  fetch(url)
    .then(response => response.blob())
    .then(blob => {
      const imageUrl = URL.createObjectURL(blob);
      scene.load.image(name, imageUrl);
      scene.load.start();

    });
}

async function loadTile(name: string, scene: Scene) {
  // given a area name, this funtion will fetch a tile from backend and store it in Phase scene, 
  // this function is async, which means we expect it to block until the fetching is completed, so the tile texture will be determined at this time, with no further changes
  let url = API_ROOT + "/text_to_tile?name="+name;
  const response = await fetch(url);
  const blob = await response.blob();
  const imageUrl = URL.createObjectURL(blob);
  scene.load.image(name, imageUrl);
  scene.load.start();
}

class GameScene extends Scene {
  private readonly squareSize = 4;
  private gridGraphics!: GameObjects.Graphics;
  private mydata: any;
  private lastTime: integer | undefined;

  constructor() {
    super('scene-game');
  }

  async load_file(){
    const environment_api = API_ROOT + "/read_environment";
    const response = await fetch(environment_api);
    const data = await response.json();
    this.mydata = data['message'];
    return Promise.resolve();
  }

  async load_tile(){
    let areas_key = Object.keys(this.mydata.areas)
    for (let i=0; i < areas_key.length; i++){
      let area_key = areas_key[i]
      let area = this.mydata.areas[area_key];
      await loadTile(area.name, this);
    }
  }

  async preload() {
    // nothing to do
  }

  async create_scene(){
    // render all areas, without any further updates

    // first load environment json
    await this.load_file();

    this.lastTime = 0;
    this.gridGraphics = this.add.graphics();

    // control the size of each pixel
    this.gridGraphics.lineStyle(5, 0xEEE8CD, 1.0); 

    // add a border for the whole world
    this.gridGraphics.strokeRect(
      ORIGIN_X - this.squareSize / 2 - 4,
      ORIGIN_Y - this.squareSize / 2 - 4,
      this.mydata.size[0] * this.squareSize + 8,
      this.mydata.size[1] * this.squareSize + 8
    );
    
    // render all areas (no further updates)
    let areas_key = Object.keys(this.mydata.areas)
    for (let i=0; i < areas_key.length; i++){
      let area_key = areas_key[i]
      let area = this.mydata.areas[area_key];

      const x = ORIGIN_X - this.squareSize /2 + this.squareSize * (area.location[0][0] -1);
      const y = ORIGIN_Y - this.squareSize / 2+ this.squareSize * (area.location[0][1] -1);
      const width = (area.location[1][0] - area.location[0][0] + 1)* this.squareSize;
      const height = (area.location[1][1] - area.location[0][1] + 1 )* this.squareSize;

      // draw the border for the upcoming block
      const graphics = this.add.graphics();
      graphics.lineStyle(4, 0xEEE8CD, 1.0);
      graphics.strokeRect(x-1, y-1, width+2, height+2);
      
      // draw a block with background image
      const tileSprite = this.add.tileSprite(x, y, width, height, area.name);
      tileSprite.setOrigin(0, 0);

      // Add the text in the middle of the strokeRect, with the text value of area.name
      this.add.text(
        100 - this.squareSize /2 + this.squareSize * (area.location[0][0] -1) + ((area.location[1][0] - area.location[0][0] )* this.squareSize)/2,
        100 - this.squareSize / 2+ this.squareSize * (area.location[0][1] -1) + ((area.location[1][1] - area.location[0][1] )* this.squareSize)/2,
        area.name,
        {
          font: '15px Arial',
          color: '#000000',
          backgroundColor: '#ffffff',
          padding: 2 as Phaser.Types.GameObjects.Text.TextPadding,
        }
      );
    }
  }

  async place_objects(){
    // update objects at a given time
    await this.load_file();

    // Loop through each object in mydata.objects
    let objects_key = Object.keys(this.mydata.objects)
    for (let i=0; i < objects_key.length; i++){
      let object_key = objects_key[i]
      let obj = this.mydata.objects[object_key];
      let obj_x = obj.location[0] + this.mydata.areas[obj.eid].location[0][0]
      let obj_y = obj.location[1] + this.mydata.areas[obj.eid].location[0][1]

      // Check if the object already exists in the scene
      let existingObj = this.children.getByName(obj.id);
      if (existingObj) {
        let existingObjSprite = existingObj as ObjectSprite;

        // If the object already exists, update its location
        existingObjSprite.x = ORIGIN_X + obj_x * this.squareSize - this.squareSize / 2;
        existingObjSprite.y = ORIGIN_Y + obj_y * this.squareSize - this.squareSize / 2;

        // update the texture (because we use non-await function to load the icon, so we need to update in latter steps)
        existingObjSprite.setTexture(obj.name);
      } else {

        // here we use non-await function call to load icons for objects
        loadIcon(obj.name, this);
        let newObj = this.add.sprite(
          ORIGIN_X + obj_x * this.squareSize  - this.squareSize / 2,
          ORIGIN_Y + obj_y * this.squareSize  - this.squareSize / 2,
          obj.name
        ) as ObjectSprite;

        // control the size of sprites in the scene
        newObj.setScale(this.squareSize / 40);
        newObj.setName(object_key);
        newObj.display_name = obj.name;

        // add tooltip listener
        newObj.setInteractive();
        newObj.on('pointerover', function () {
          showTooltip(newObj);
        });
        newObj.on('pointerout', function () {
          hideTooltip(newObj);
        });
      }
    }
  }

  async create() {
    resize_canvas();

    // load environment json and tile at start (blocking function call)
    await this.load_file();
    await this.load_tile();
    this.lastTime = 0.0;
    this.create_scene();
    this.place_objects();

  }

  // Use the update() function to update the square's locationition every 1 second to the left
  update(time: integer) {

      // Set the scene's time event to update the square's locationition every 1 second to the left
      const lastTime = this.lastTime as integer;
      if (time > lastTime + 1000) {
        
        this.place_objects()
        this.lastTime = time
      }
  }
}

const config = {
  type: WEBGL,
  zoom:Phaser.AUTO,
  canvas,
  physics: {
    default: 'arcade',
    arcade: {
      gravity: { y: 0 },
    }
  },
  backgroundColor: '#ffffff',
  scene: [GameScene]
};

function resize_canvas() {
  // resize the canvas according to current window size
  const width = Math.max(window.innerWidth * 0.7);
  const height = Math.max(window.innerWidth * HEIGHT_WIDTH_RATIO * 0.7);
  canvas.style.width = width + 'px';
  canvas.style.height = height + 'px';
}

// resize the game object as windows resize
window.addEventListener('resize', function () {
  resize_canvas();
});

new Game(config);

