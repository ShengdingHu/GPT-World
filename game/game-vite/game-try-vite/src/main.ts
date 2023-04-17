import './style.css';
import { Scene, Game, WEBGL, GameObjects} from 'phaser';



const canvas = document.getElementById('game') as HTMLCanvasElement;

class GameScene extends Scene {
  private readonly gridWidth = 20;
  private readonly gridHeight = 10;
  private readonly squareSize = 50;
  private gridGraphics!: GameObjects.Graphics;
  private square!: GameObjects.Sprite;


  private currentCol = 1;
  private currentRow = 1;

  constructor() {
    super('scene-game');
  }

  create() {
    this.lastTime = 0;

    // Create graphics object for the grid
    this.gridGraphics = this.add.graphics();

    const mydata = {
      "name": "Happy Farm",
      "id": "e_001",
      "size": [10, 20],
      "areas": [
          {"pos": [[1,1],[9,10]], "name":"farm", "id": "e_002", "border": 0},
          {"pos": [[11,1],[20,10]], "name":"house", "id": "e_003", "border": 2}
      ],
      "object": [
          {"id": "o_001", "name": "tree", "eid": "e_002", "location": [[1,1]]},
          {"id": "o_002", "name": "tree", "eid": "e_002", "location": [[1,3]]},
          {"id": "o_003", "name": "bed", "eid": "e_003", "location": [[1,1],[3,6]]},
          {"id": "a_001", "name": "Alice", "eid": "e_001", "location": [[10,3]]},
          {"id": "a_002", "name": "Bob", "eid": "e_001", "location": [[10,5]]}
      ]
    };
    
    console.log(mydata.areas);

    this.gridGraphics.lineStyle(5, 0x080808, 1.0);
    this.gridGraphics.strokeRect(
      100 - this.squareSize / 2 - 4,
      100 - this.squareSize / 2 - 4,
      mydata.size[1] * this.squareSize + 8,
      mydata.size[0] * this.squareSize + 8
    );


    for (let i=0; i < mydata.areas.length; i++){
      let area = mydata.areas[i];
      this.gridGraphics.fillStyle(2, 0xaaaaaa, 1)
      this.gridGraphics.fillRect(
        100 - this.squareSize /2 + this.squareSize * (area.pos[0][0] -1),
        100 - this.squareSize / 2+ this.squareSize * (area.pos[0][1] -1),
        (area.pos[1][0] - area.pos[0][0] + 1)* this.squareSize,
        (area.pos[1][1] - area.pos[0][1] + 1 )* this.squareSize
      );
      // Add the text in the middle of the strokeRect, with the text value of area.name
      this.add.text(
        100 - this.squareSize /2 + this.squareSize * (area.pos[0][0] -1) + ((area.pos[1][0] - area.pos[0][0] )* this.squareSize)/2,
        100 - this.squareSize / 2+ this.squareSize * (area.pos[0][1] -1) + ((area.pos[1][1] - area.pos[0][1] )* this.squareSize)/2,
        area.name,
        {
          font: '20px Arial',
          fill: '#000000',
          border: null
        }
      );
    }

        // Create a sprite object for the square
        this.square = this.add.sprite(
            100 - this.squareSize / 2,
            100 - this.squareSize / 2,
            'square'
          );
        this.square.setScale(this.squareSize / 100);


  }

    /// Use the update() function to update the square's position every 1 second to the left
  update(time, delta) {
      // Set the scene's time event to update the square's position every 1 second to the left
      console.log(time)
      console.log(this.lastTime)
      if (time > this.lastTime + 1000) {
        this.square.x += 10;
        this.lastTime = time;
      }
  }
}

const config = {
  type: WEBGL,
  width: window.innerWidth,
  height: window.innerHeight,
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

new Game(config);
