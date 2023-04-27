import './style.css';
import { Scene, Game, WEBGL, GameObjects} from 'phaser';
import { io, Socket } from "socket.io-client";


const API_ROOT = "http://localhost:5001";


///////////////// Implement UI Logging function /////////////////
interface Message {
  text: string;
  sender: string;
  time: Date;
}

const messagesElement = document.getElementById('messages')!;
// const inputElement = document.getElementById('input') as HTMLInputElement;
// const sendButton = document.getElementById('send')!;

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

// normal messages
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

//////////////////////////////////////////////////////////////////



////////////////// Implement Game Scene /////////////////////

const canvas = document.getElementById('game') as HTMLCanvasElement;
const ORIGIN_X = 100;
const ORIGIN_Y = 100;

function loadIcon(name: string, scene: Scene) {
  let url = API_ROOT+"/text_to_icon?name="+name;
  fetch(url)
    .then(response => response.blob())
    .then(blob => {
      const imageUrl = URL.createObjectURL(blob);
      scene.load.image(name, imageUrl);
      scene.load.start();

    });
}

async function loadTile(name: string, scene: Scene) {
  let url = API_ROOT+"/text_to_tile?name="+name;
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
    const response = await fetch(API_ROOT+"/read_environment");
    // console.log(response);
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
    
  }

  async create_scene(){
    await this.load_file();

    this.lastTime = 0;
    this.gridGraphics = this.add.graphics();

    // console.log(this.mydata.areas);

    this.gridGraphics.lineStyle(4, 0xEEE8CD, 1.0);
    this.gridGraphics.strokeRect(
      ORIGIN_X - this.squareSize / 2 - 4,
      ORIGIN_Y - this.squareSize / 2 - 4,
      this.mydata.size[0] * this.squareSize + 8,
      this.mydata.size[1] * this.squareSize + 8
    );

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
          fill: '#000000',
          backgroundColor: '#ffffff',
          padding: 2
        }
      );
    }
  }

  async place_objects(){
    await this.load_file();
    // Loop through each object in mydata.objects

    let objects_key = Object.keys(this.mydata.objects)
    for (let i=0; i < objects_key.length; i++){
      let object_key = objects_key[i]
      let obj = this.mydata.objects[object_key];

      let obj_x = obj.location[0] + this.mydata.areas[obj.eid].location[0][0]
      let obj_y = obj.location[1] + this.mydata.areas[obj.eid].location[0][1]

      // console.log("obj_x, obj_y", obj_x, obj_y)
      // Check if the object already exists in the scene
      let existingObj = this.children.getByName(obj.id);
      if (existingObj) {
        
        // If the object already exists, update its location
        existingObj.x = ORIGIN_X + obj_x * this.squareSize - this.squareSize / 2;
        existingObj.y = ORIGIN_Y + obj_y * this.squareSize - this.squareSize / 2;
        let existingObj_title = this.children.getByName(obj.id+"_title");
        existingObj_title.x = existingObj.x;
        existingObj_title.y = existingObj.y;
        existingObj.setTexture(obj.name);

      } else {

        loadIcon(obj.name, this);

        let newObj = this.add.sprite(
          ORIGIN_X + obj_x * this.squareSize  - this.squareSize / 2,
          ORIGIN_Y + obj_y * this.squareSize  - this.squareSize / 2,
          obj.name
        );

        newObj.setScale(this.squareSize / 40);
        newObj.setName(object_key);
        // Change the color of the sprite to white
        newObj.setTint(0xffffff);
        // Add text to the sprite with the value of obj.name
        let obj_title = this.add.text(
          newObj.x,
          newObj.y,
          obj.name,
          {
            font: '15px Arial',
            color: '#000000',
            backgroundColor: '#ffffff',
            padding: 2
          }
        );
        obj_title.setName(object_key+"_title");

      }
    }
  }

  async create() {
    const width = Math.max(window.innerWidth * 0.7, 800);
    const height = Math.max(window.innerHeight * 0.7, 600);
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    
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
        console.log("Update")
        this.place_objects()
        this.lastTime = time
      }
  }
}

const config = {
  type: WEBGL,
  // width: window.innerWidth,
  // height: window.innerHeight,
  canvas,

  physics: {
    default: 'arcade',
    arcade: {
      gravity: { y: 0 },
      // debug: true
    }
  },
  backgroundColor: '#ffffff',
  scene: [GameScene]
};

var game = new Game(config);

// resize the game object as windows resize
window.addEventListener('resize', function () {
  const width = Math.max(window.innerWidth * 0.7, 800);
  const height = Math.max(window.innerHeight * 0.7, 600);
  canvas.style.width = width + 'px';
  canvas.style.height = height + 'px';
});

//////////////////////////////////