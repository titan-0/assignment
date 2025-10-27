import { useEffect, useMemo, useRef, useState } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/live';

export function useLiveFeed() {
  const [status, setStatus] = useState('disconnected'); // 'connecting' | 'connected' | 'disconnected'
  const [prices, setPrices] = useState({}); // { ticker: { price, prev, open } }
  const [orderUpdates, setOrderUpdates] = useState([]); // recent order updates
  const [trades, setTrades] = useState([]); // new trades appended

  const wsRef = useRef(null);
  const reconnectRef = useRef(null);

  useEffect(() => {
    function connect() {
      setStatus('connecting');
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;
      ws.onopen = () => setStatus('connected');
      ws.onclose = () => {
        setStatus('disconnected');
        // Try to reconnect after a short delay
        reconnectRef.current = setTimeout(connect, 1500);
      };
      ws.onerror = () => ws.close();
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          switch (msg.type) {
            case 'price_update': {
              setPrices((prev) => {
                const prevTicker = prev[msg.ticker]?.price ?? null;
                const prevOpen = prev[msg.ticker]?.open ?? null;
                const openVal = msg.open != null ? msg.open : prevOpen;
                return {
                  ...prev,
                  [msg.ticker]: { price: msg.price, prev: prevTicker, open: openVal },
                };
              });
              break;
            }
            case 'order_update': {
              setOrderUpdates((arr) => [{ ...msg, _ts: Date.now() }, ...arr].slice(0, 50));
              break;
            }
            case 'new_trade': {
              setTrades((arr) => [{ ...msg, _ts: Date.now() }, ...arr].slice(0, 200));
              break;
            }
            default:
              break;
          }
        } catch (_) {
          // ignore parse errors
        }
      };
    }

    connect();
    return () => {
      clearTimeout(reconnectRef.current);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return {
    status,
    prices,
    orderUpdates,
    newTrades: trades,
  };
}
