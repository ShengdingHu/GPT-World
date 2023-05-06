import React from 'react';
import './App.css';
import GameArea from './components/GameArea';
import Chat from "./components/Chat";


function App() {
  return (
    <div className="app">
      <div className="header">Welcome to GPTWorld</div>
      <div className="container">
        <div className="left-column">
          <div className="game-area-container">
            <div className="game-area-scroll">
              <GameArea />
            </div>
          </div>
        </div>
        <div className="right-column">
          <Chat />
        </div>
      </div>
    </div>
  );
}


export default App;
