import './index.css';
import WebSocketStatus from './components/WebSocketStatus';
import TickerPanel from './components/TickerPanel';
import OrdersTable from './components/OrdersTable';
import TradesTable from './components/TradesTable';
import OrderEntryForm from './components/OrderEntryForm';
import { useEffect, useMemo, useState } from 'react';
import { fetchOpenOrders, fetchRecentTrades, fetchTickers, fetchPriceHistory } from './lib/api';
import { useLiveFeed } from './lib/useLiveFeed';

function App() {
  const [orders, setOrders] = useState([]);
  const [trades, setTrades] = useState([]);
  const [tickers, setTickers] = useState([]);
  const [highlightId, setHighlightId] = useState(null);
  const [historyBySymbol, setHistoryBySymbol] = useState({}); // sym -> [{price, timestamp}]

  const { status, prices, orderUpdates, newTrades } = useLiveFeed();

  // Initial loads
  useEffect(() => {
    refreshOrders();
    refreshTrades();
    fetchTickers()
      .then(async (tks) => {
        setTickers(tks);
        // Prefetch history for small sparkline
        try {
          const entries = await Promise.all(
            tks.map(async (t) => [t.symbol, await fetchPriceHistory(t.symbol, 10)])
          );
          const hist = {};
          for (const [sym, ticks] of entries) {
            hist[sym] = ticks;
          }
          setHistoryBySymbol(hist);
        } catch {
          // ignore history prefetch errors
        }
      })
      .catch(() => {
        // swallow; fallback handled by separate effect
      });
  }, []);

  // Fallback: if tickers haven't loaded but we have prices or orders, derive symbols once
  useEffect(() => {
    if (Array.isArray(tickers) && tickers.length > 0) return;
    const syms = Object.keys(prices);
    const orderSyms = new Set(orders.map((o) => o.ticker));
    const derived = syms.length ? syms : Array.from(orderSyms);
    if (derived.length) {
      setTickers(derived.map((s) => ({ symbol: s })));
    }
  }, [tickers, prices, orders]);

  // Apply live order updates (highlight row)
  useEffect(() => {
    if (!orderUpdates.length) return;
    const u = orderUpdates[0];
    setHighlightId(u.order_id);
    // Re-fetch orders for latest statuses
    refreshOrders();
    const t = setTimeout(() => setHighlightId(null), 1500);
    return () => clearTimeout(t);
  }, [orderUpdates]);

  // Append new trades from WS to top
  useEffect(() => {
    if (!newTrades.length) return;
    setTrades((prev) => {
      const seen = new Set(prev.map((t) => t.trade_id));
      const added = new Set();
      const fresh = newTrades
        .filter((t) => {
          if (seen.has(t.trade_id) || added.has(t.trade_id)) return false;
          added.add(t.trade_id);
          return true;
        })
        .map((t) => ({
          trade_id: t.trade_id,
          order_id: t.order_id,
          tradingsymbol: t.tradingsymbol,
          product: 'MIS',
          quantity: t.quantity,
          average_price: t.price,
          transaction_type: t.transaction_type,
          fill_timestamp: t.fill_timestamp,
        }));
      return [...fresh, ...prev].slice(0, 100);
    });
  }, [newTrades]);

  // Track price history for sparkline (cap 10)
  useEffect(() => {
    const syms = Object.keys(prices);
    if (!syms.length) return;
    setHistoryBySymbol((prev) => {
      const next = { ...prev };
      for (const sym of syms) {
        if (prices[sym]?.price == null) continue;
        const arr = (next[sym] || []).slice(-9);
        arr.push({ price: prices[sym].price, timestamp: Date.now() });
        next[sym] = arr;
      }
      return next;
    });
  }, [prices]);

  async function refreshOrders() {
    try {
      const data = await fetchOpenOrders();
      setOrders(data);
    } catch (e) {
      // noop
    }
  }
  async function refreshTrades() {
    try {
      const data = await fetchRecentTrades();
      setTrades(data);
    } catch (e) {
      // noop
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold">Deccan Research Capital — Trading Dashboard</h1>
          <WebSocketStatus status={status} />
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6 space-y-6">
        <section>
          <h2 className="text-sm font-semibold text-slate-600 mb-2">Live Ticker Prices</h2>
          <TickerPanel prices={prices} tickers={tickers} historyBySymbol={historyBySymbol} />
        </section>

        <section className="grid grid-cols-1 gap-6">
          <OrderEntryForm tickers={tickers} onPlaced={refreshOrders} />
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <OrdersTable orders={orders} onRefresh={refreshOrders} lastHighlightId={highlightId} />
          <TradesTable trades={trades} onRefresh={refreshTrades} />
        </section>
      </main>

      <footer className="text-center py-4 text-xs text-slate-500">Built with FastAPI, WebSocket, React + Tailwind</footer>
    </div>
  );
}

export default App;
