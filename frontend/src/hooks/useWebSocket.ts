import { useEffect, useState, useRef, useCallback } from 'react';

export interface WebSocketEventMessage {
  event_id?: string;
  event_type?: string;
  timestamp?: string;
  payload?: any;
  type?: string;
  message?: string;
}

export function useWebSocket(url?: string) {
  const wsUrl = url || (typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000/ws/events`
    : 'ws://localhost:8000/ws/events');

  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastEvent, setLastEvent] = useState<WebSocketEventMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let socket: WebSocket;
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      try {
        socket = new WebSocket(wsUrl);
        wsRef.current = socket;

        socket.onopen = () => {
          setIsConnected(true);
          console.log('[SentinelML WS] Connected to real-time events stream:', wsUrl);
        };

        socket.onmessage = (event) => {
          try {
            const data: WebSocketEventMessage = JSON.parse(event.data);
            setLastEvent(data);
          } catch (e) {
            console.warn('[SentinelML WS] Received non-JSON frame:', event.data);
          }
        };

        socket.onerror = (err) => {
          console.warn('[SentinelML WS] Error on connection:', err);
        };

        socket.onclose = () => {
          setIsConnected(false);
          // Try reconnecting in 5s
          reconnectTimeout = setTimeout(connect, 5000);
        };
      } catch (err) {
        console.warn('[SentinelML WS] Socket initialization failed:', err);
      }
    };

    connect();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (socket) {
        socket.close();
      }
    };
  }, [wsUrl]);

  const sendPing = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'PING' }));
    }
  }, []);

  return { isConnected, lastEvent, sendPing };
}

export default useWebSocket;
