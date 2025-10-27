import { useEffect, useState } from 'react';
import { createOrder } from '../lib/api';

export default function OrderEntryForm({ tickers = [], onPlaced }) {
  const [ticker, setTicker] = useState('');
  const [action, setAction] = useState('BUY');
  const [quantity, setQuantity] = useState(25);
  const [price, setPrice] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    // Initialize selected ticker when tickers load; safe to depend on `ticker`
    // because once it's set, the condition prevents re-setting.
    if (!ticker && tickers.length) setTicker(tickers[0].symbol);
  }, [tickers, ticker]);

  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setMsg('');
    try {
      const payload = {
        ticker,
        action,
        quantity: Number(quantity),
        price: Number(price),
      };
      const res = await createOrder(payload);
      setMsg(`Order ${res.order_id} placed.`);
      setPrice('');
      if (onPlaced) onPlaced(res);
    } catch (err) {
      setMsg('Failed to place order');
    } finally {
      setBusy(false);
    }
  }

  const hasTickers = Array.isArray(tickers) && tickers.length > 0;

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-md border border-slate-200 shadow-sm p-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-slate-700">New Order</h3>
        {msg && <span className="text-xs text-slate-500">{msg}</span>}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div>
          <label className="block text-xs text-slate-500 mb-1">Ticker</label>
          {hasTickers ? (
            <select value={ticker} onChange={(e) => setTicker(e.target.value)} className="w-full border border-slate-300 rounded-md px-2 py-1.5">
              {tickers.map((t) => (
                <option key={t.symbol} value={t.symbol}>{t.symbol}</option>
              ))}
            </select>
          ) : (
            <input disabled className="w-full border border-slate-300 rounded-md px-2 py-1.5 bg-slate-50 text-slate-400" placeholder="Loading tickers..." />
          )}
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Action</label>
          <select value={action} onChange={(e) => setAction(e.target.value)} className="w-full border border-slate-300 rounded-md px-2 py-1.5">
            <option>BUY</option>
            <option>SELL</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Quantity</label>
          <input type="number" value={quantity} min={1} onChange={(e) => setQuantity(e.target.value)} className="w-full border border-slate-300 rounded-md px-2 py-1.5" />
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Price</label>
          <input type="number" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)} className="w-full border border-slate-300 rounded-md px-2 py-1.5" />
        </div>
        <div className="flex items-end">
          <button disabled={busy || !hasTickers || !ticker} type="submit" className="w-full md:w-auto px-3 py-2 rounded-md bg-slate-800 text-white hover:bg-slate-700 disabled:opacity-50">Place</button>
        </div>
      </div>
      {!hasTickers && (
        <div className="mt-2 text-xs text-slate-500">Tickers are loading from the server…</div>
      )}
    </form>
  );
}
