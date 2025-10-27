import { useMemo } from 'react';

function Sparkline({ data = [], width = 80, height = 24, stroke = '#64748b' }) {
  if (!data.length) return <svg width={width} height={height} />;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = Math.max(1e-6, max - min);
  const stepX = width / Math.max(1, data.length - 1);
  const points = data.map((v, i) => {
    const x = i * stepX;
    const y = height - ((v - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');
  return (
    <svg width={width} height={height}>
      <polyline fill="none" stroke={stroke} strokeWidth="2" points={points} />
    </svg>
  );
}

export default function TickerPanel({ prices, tickers, historyBySymbol = {} }) {
  const symbols = useMemo(() => {
    if (tickers && tickers.length) return tickers.map((t) => t.symbol);
    return Object.keys(prices);
  }, [prices, tickers]);

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {symbols.map((sym) => {
        const live = prices[sym] || {};
        const hist = historyBySymbol[sym] || [];
        const pLive = live.price ?? null;

        
        const histCurr = hist.length >= 1 ? hist[hist.length - 1]?.price ?? null : null;

        const p = pLive != null ? pLive : histCurr;

        const open = live.open ?? (hist.length ? hist[0]?.price ?? null : null);

        const changeDay = p != null && open != null ? (p - open) : 0;
        const denom = open != null && open !== 0 ? open : (p || 1);
        const pct = (changeDay / denom) * 100;
        const pctStr = Number.isFinite(pct)
          ? (denom > 1000 ? pct.toFixed(3) : pct.toFixed(2))
          : '0.00';
        
        const flash = changeDay > 0 ? 'ring-1 ring-green-300' : changeDay < 0 ? 'ring-1 ring-red-300' : '';
        return (
          <div key={sym} className={`rounded-md bg-white shadow-sm p-3 border border-slate-200 ${flash}`}>
            <div className="text-sm font-medium text-slate-700">{sym}</div>
            <div className="mt-1 flex items-baseline gap-2">
              <div className="text-xl font-semibold tabular-nums">{p != null ? Number(p).toFixed(2) : '—'}</div>
              <div className={`text-sm ${changeDay > 0 ? 'text-green-600' : changeDay < 0 ? 'text-red-600' : 'text-slate-500'}`}>
                {p != null ? `${changeDay >= 0 ? '+' : ''}${(changeDay || 0).toFixed(2)} (${pct >= 0 ? '+' : ''}${pctStr}%)` : ''}
              </div>
            </div>
            <div className="mt-2">
              <Sparkline data={(historyBySymbol[sym] || []).map((d) => d.price)} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
