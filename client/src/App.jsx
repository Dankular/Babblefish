// Root component with routing
import { useState } from 'react';
import ModelLoadingPage from './pages/ModelLoadingPage';
import JoinPage from './pages/JoinPage';
import RoomPage from './pages/RoomPage';
import './styles/globals.css';

function App() {
  const [currentPage, setCurrentPage] = useState('loading'); // Start with model loading
  const [roomConfig, setRoomConfig] = useState(null);
  const [ttsEngine, setTtsEngine] = useState(null);

  const handleModelsLoaded = ({ engine }) => {
    console.log(`[App] Models loaded with engine: ${engine}`);
    setTtsEngine(engine);
    setCurrentPage('join');
  };

  const handleJoin = async (config) => {
    setRoomConfig(config);
    setCurrentPage('room');
  };

  const handleLeave = () => {
    setRoomConfig(null);
    setCurrentPage('join');
  };

  return (
    <div className="app">
      {currentPage === 'loading' && (
        <ModelLoadingPage onComplete={handleModelsLoaded} />
      )}

      {currentPage === 'join' && (
        <JoinPage onJoin={handleJoin} ttsEngine={ttsEngine} />
      )}

      {currentPage === 'room' && roomConfig && (
        <RoomPage roomConfig={roomConfig} onLeave={handleLeave} />
      )}
    </div>
  );
}

export default App;
