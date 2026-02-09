// WebSocket manager with reconnect
export class WebSocketManager {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000; // Start with 1 second
    this.maxReconnectDelay = 30000; // Max 30 seconds
    this.reconnectTimer = null;
    this.isIntentionallyClosed = false;
    this.heartbeatInterval = null;
    this.heartbeatTimer = 30000; // 30 seconds

    // Callbacks
    this.onOpen = null;
    this.onMessage = null;
    this.onClose = null;
    this.onError = null;
    this.onReconnecting = null;
  }

  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    this.isIntentionallyClosed = false;

    try {
      console.log(`Connecting to ${this.url}...`);
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;

        if (this.onOpen) {
          this.onOpen();
        }

        this.startHeartbeat();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Handle heartbeat pong
          if (data.type === 'pong') {
            return;
          }

          if (this.onMessage) {
            this.onMessage(data);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        this.stopHeartbeat();

        if (this.onClose) {
          this.onClose(event);
        }

        if (!this.isIntentionallyClosed) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (this.onError) {
          this.onError(error);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      if (!this.isIntentionallyClosed) {
        this.scheduleReconnect();
      }
    }
  }

  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    if (this.onReconnecting) {
      this.onReconnecting(this.reconnectAttempts, delay);
    }

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  send(data) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected, cannot send message');
      return false;
    }

    try {
      this.ws.send(JSON.stringify(data));
      return true;
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      return false;
    }
  }

  close() {
    this.isIntentionallyClosed = true;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    console.log('WebSocket closed intentionally');
  }

  startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      this.send({ type: 'ping', timestamp: Date.now() });
    }, this.heartbeatTimer);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  getState() {
    return {
      connected: this.ws?.readyState === WebSocket.OPEN,
      reconnectAttempts: this.reconnectAttempts,
      readyState: this.ws?.readyState
    };
  }
}
