import { useEffect, useRef, useState, useCallback } from "react";

export default function useWebSocket() {
  const wsRef = useRef(null);
  const [lastEvent, setLastEvent] = useState(null);
  const [connected, setConnected] = useState(false);
  const listenersRef = useRef({});

  const connect = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      setTimeout(connect, 3000);
    };
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastEvent(data);
        const handlers = listenersRef.current[data.event];
        if (handlers) {
          handlers.forEach((fn) => fn(data.data));
        }
      } catch {}
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  const on = useCallback((event, handler) => {
    if (!listenersRef.current[event]) {
      listenersRef.current[event] = [];
    }
    listenersRef.current[event].push(handler);
    return () => {
      listenersRef.current[event] = listenersRef.current[event].filter(
        (fn) => fn !== handler
      );
    };
  }, []);

  return { connected, lastEvent, on };
}
