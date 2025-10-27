const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export async function fetchOpenOrders() {
  const res = await fetch(`${API_BASE}/orders/open`);
  if (!res.ok) throw new Error('Failed to fetch open orders');
  const data = await res.json();
  return data.orders || [];
}

export async function fetchRecentTrades() {
  const res = await fetch(`${API_BASE}/trades/recent`);
  if (!res.ok) throw new Error('Failed to fetch recent trades');
  const data = await res.json();
  return data.trades || [];
}

export async function fetchTickers() {
  const res = await fetch(`${API_BASE}/tickers`);
  if (!res.ok) throw new Error('Failed to fetch tickers');
  const data = await res.json();
  return data.tickers || [];
}

export function formatTime(ts) {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    return d.toLocaleString();
  } catch {
    return String(ts);
  }
}

// ---- Extras ----
export async function createOrder(payload) {
  const res = await fetch(`${API_BASE}/orders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create order');
  return res.json();
}

export async function patchOrder(orderId, payload) {
  const res = await fetch(`${API_BASE}/orders/${orderId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update order');
  return res.json();
}

export async function fetchPriceHistory(symbol, limit = 10) {
  const res = await fetch(`${API_BASE}/prices/${encodeURIComponent(symbol)}?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch price history');
  const data = await res.json();
  return data.ticks || [];
}
