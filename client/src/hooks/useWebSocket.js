// WebSocket connection hook
import { useState, useEffect, useCallback, useRef } from 'react';
import { WebSocketManager } from '../network/websocket';

export function useWebSocket(url) {
  const [status, setStatus] = useState('disconnected'); // 'disconnected', 'connecting', 'connected', 'reconnecting'
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocketManager(url);
    wsRef.current = ws;

    ws.onOpen = () => {
      setStatus('connected');
      setError(null);
    };

    ws.onMessage = (message) => {
      setMessages(prev => [...prev, message]);
    };

    ws.onClose = (event) => {
      if (event.code !== 1000) {
        setStatus('disconnected');
      }
    };

    ws.onError = (err) => {
      setError(err.message || 'WebSocket error');
      setStatus('disconnected');
    };

    ws.onReconnecting = (attempt, delay) => {
      setStatus('reconnecting');
    };

    setStatus('connecting');
    ws.connect();

    return () => {
      ws.close();
    };
  }, [url]);

  const send = useCallback((message) => {
    if (wsRef.current) {
      return wsRef.current.send(message);
    }
    return false;
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    status,
    messages,
    error,
    send,
    clearMessages
  };
}
