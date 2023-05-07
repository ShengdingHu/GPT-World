import React, { useEffect, useState } from 'react';
import './GameArea.css';
import './Border.css';

const API_ROOT = '';
// const API_ROOT = 'http://localhost:5001/';


const ORIGIN_X = 10;
const ORIGIN_Y = 10;


function fixedEncodeURIComponent (str) {
    return encodeURIComponent(str).replace(/[!'()*]/g, function(c) {
      return '%' + c.charCodeAt(0).toString(16);
    });
  }


const GameArea = () => {
  const [gameData, setGameData] = useState(null);
  const scale = 4;

  const loadFile = async () => {
    const environmentApi = API_ROOT + '/read_environment';
    const response = await fetch(environmentApi);
    const data = await response.json();
    setGameData(data.message);
  };


  useEffect(() => {
    if (!gameData) {
      loadFile();
      return;
    }
  }, [gameData]);

  useEffect(() => {
    const updateData = async () => {
      await loadFile();
    };

    const intervalId = setInterval(updateData, 1000);
    return () => {
      clearInterval(intervalId);
    };
  }, []);

  const getImageSize = (object) => {
    console.log(object)
    if ('size' in object) {
      return { width: object.size[0] * scale, height: object.size[1] * scale};
    } else {
      return { width: 5*scale, height: 5*scale };
    }
  };

  const getZIndex = (object) => {
    if (object.id.startsWith("a")) {
      return { zIndex: 1000 };
    } else {
      return { zIndex: 0 };
    }
  };

  return (
    <div className="game-container">
      {gameData &&
        Object.values(gameData.areas).map((area, index) => (
            <div
                key={`area-${index}-${area.name}`}
                className="area wall-div"
                style={{
                    backgroundImage: `url(${API_ROOT}/text_to_tile?name=${fixedEncodeURIComponent(
                        area.name
                    )})`,
                    backgroundRepeat: 'repeat',
                    left: (ORIGIN_X + area.location[0][0]) * scale,
                    top: (ORIGIN_Y + area.location[0][1]) * scale,
                    width: (area.location[1][0] - area.location[0][0]) * scale,
                    height: (area.location[1][1] - area.location[0][1]) * scale,
                }}
          >
            <div className="wall-topborder"></div>
            <div className="wall-top"></div>
            <div className="wall-left"></div>
            <div className="wall-right"></div>
            <div className="wall-bottom-left"></div>
            <div className="wall-bottom-right"></div>

            <span className="area-label" data-tooltip={area.name}>{area.name}</span>
          </div>
        ))}
      {gameData &&
        Object.values(gameData.objects).map((object, index) => (
            <div 
                className="object-container"
                key={`object-container-${index}-${object.name}`}
                style={{
                    left: (ORIGIN_X + object.location[0]) * scale,
                    top: (ORIGIN_Y + object.location[1]) * scale,
                }}
            >
                <img
                    className="object"
                    src={`${API_ROOT}/text_to_icon?name=${fixedEncodeURIComponent(object.name)}`}
                    alt={object.name}
                    style={{...getImageSize(object) , ...getZIndex(object)}}
                />
                <span className="object-tooltip" data-tooltip={object.name}>{object.name}</span>
            </div>
            
        ))
        }
    
    </div>
  );
};

export default GameArea;
