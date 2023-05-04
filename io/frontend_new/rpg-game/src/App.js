import React from 'react';
import './App.css';
import GameArea from './components/GameArea';
import Chat from "./components/Chat";


function App() {
  return (
    <div>
      <div>WorldGPT User Interface</div>
      <div className="container">
        <div className="left-column">
          <GameArea />
        </div>
        <div className="right-column">
          <Chat />
        </div>
      </div>
    </div>
  );
}

export default App;
