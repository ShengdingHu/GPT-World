import './style.css';
import { Scene, Game, WEBGL, GameObjects } from 'phaser';


const canvas = document.getElementById('game') as HTMLCanvasElement;

class GameScene extends Scene {
  private readonly gridWidth = 20;
  private readonly gridHeight = 10;
  private readonly squareSize = 50;
  private gridGraphics!: GameObjects.Graphics;
  private square!: GameObjects.Graphics;


  private currentCol = 1;
  private currentRow = 1;

  constructor() {
    super('scene-game');
  }

  create() {
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
      100 - this.squareSize / 2,
      100 - this.squareSize / 2,
      mydata.size[1] * this.squareSize,
      mydata.size[0] * this.squareSize
    );


    for (let i=0; i < mydata.areas.length; i++){
      let area = mydata.areas[i];
      this.gridGraphics.lineStyle(5, 0x080808, 1.0);
      this.gridGraphics.lineStyle(2, 0xfffff, 1)
      this.gridGraphics.strokeRect(
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

    // this.gridGraphics.lineStyle(2, 0xfffff, 1);

    // // Loop through each row and column of the grid
    // for (let row = 0; row < this.gridHeight; row++) {
    //   for (let col = 0; col < this.gridWidth; col++) {
    //     // Calculate the position of the current grid square
    //     const xPos = 100 + col * this.squareSize;
    //     const yPos = 100 + row * this.squareSize;

    //     // Draw the border of the current grid square
    //     this.gridGraphics.strokeRect(
    //       xPos - this.squareSize / 2,
    //       yPos - this.squareSize / 2,
    //       this.squareSize,
    //       this.squareSize
    //     )

    //     // Use black border for the strokeRect


    //     // Create a text object for the current grid square
    //     const text = this.add.text(
    //       xPos,
    //       yPos,
    //       `${col},${row}`,
    //       {
    //         font: '10px Arial',
    //         fill: '#000000',
    //         border: null
    //       }
    //     );
    //     text.setOrigin(0.5, 0.5);

        // If this is the (1,1) square, create a graphics object for it

        this.square = this.add.graphics();
        this.square.fillStyle(0xff0000, 1);
        this.square.fillRect(
          100 - this.squareSize / 2,
          100 - this.squareSize / 2,
          this.squareSize,
          this.squareSize
        );
        this.currentCol = 1;
        this.currentRow = 1;
      
  

    // Move the square to (5,1) and then to (5,5)
    this.tweens.add({
      targets: this.square,
      x: 450,
      y: 150,
      ease: 'Linear',
      duration: 1000,
      onComplete: () => {
        this.currentCol = 5;
        this.currentRow = 1;

        this.tweens.add({
          targets: this.square,
          x: 450,
          y: 450,
          ease: 'Linear',
          duration: 1000,
          onComplete: () => {
            this.currentRow = 5;
          }
        });
      }
    });
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
