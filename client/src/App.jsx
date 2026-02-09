// Root component with routing
import { useState } from 'react';
import JoinPage from './pages/JoinPage';
import RoomPage from './pages/RoomPage';
import './styles/globals.css';

function App() {
  const [currentPage, setCurrentPage] = useState('join');
  const [roomConfig, setRoomConfig] = useState(null);

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
      {currentPage === 'join' && (
        <JoinPage onJoin={handleJoin} />
      )}

      {currentPage === 'room' && roomConfig && (
        <RoomPage roomConfig={roomConfig} onLeave={handleLeave} />
      )}
    </div>
  );
}

export default App;
