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
    this.gridGraphics.lineStyle(2, 0xfffff, 1);

    // Loop through each row and column of the grid
    for (let row = 0; row < this.gridHeight; row++) {
      for (let col = 0; col < this.gridWidth; col++) {
        // Calculate the position of the current grid square
        const xPos = 100 + col * this.squareSize;
        const yPos = 100 + row * this.squareSize;

        // Draw the border of the current grid square
        this.gridGraphics.strokeRect(
          xPos - this.squareSize / 2,
          yPos - this.squareSize / 2,
          this.squareSize,
          this.squareSize
        );

        // Create a text object for the current grid square
        const text = this.add.text(
          xPos,
          yPos,
          `${col},${row}`,
          {
            font: '10px Arial',
            fill: '#000000',
            border: null
          }
        );
        text.setOrigin(0.5, 0.5);

        // If this is the (1,1) square, create a graphics object for it
        if (col === 1 && row === 1) {
          this.square = this.add.graphics();
          this.square.fillStyle(0xff0000, 1);
          this.square.fillRect(
            xPos - this.squareSize / 2,
            yPos - this.squareSize / 2,
            this.squareSize,
            this.squareSize
          );
          this.currentCol = col;
          this.currentRow = row;
        }
      }
    }

        json.object[i];
        var eid = obj.eid;
        var x = obj.location[0][0];
        var y = obj.location[0][1];
        var spriteName = obj.name;

        // 创建对象精灵
        var sprite = this.add.sprite(x * 32, y * 32, spriteName);

        // 将对象精灵添加到对应的区域中
        for (var x1 = x; x1 <= x + 1; x1++) {
            for (var y1 = y; y1 <= y + 1; y1++) {
                if (grid[x1][y1] === eid) {
                    this.children.add(sprite);
                }
            }
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
