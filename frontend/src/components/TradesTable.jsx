import { formatTime } from '../lib/api';

export default function TradesTable({ trades, onRefresh }) {
  return (
    <div className="bg-white rounded-md border border-slate-200 shadow-sm">
      <div className="p-3 flex items-center justify-between">
        <h3 className="font-semibold text-slate-700">Recent Trades</h3>
        <button onClick={onRefresh} className="px-3 py-1.5 text-sm rounded-md bg-slate-800 text-white hover:bg-slate-700">Refresh</button>
      </div>
      <div className="overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-3 py-2 text-left">Trade ID</th>
              <th className="px-3 py-2 text-left">Order ID</th>
              <th className="px-3 py-2 text-left">Symbol</th>
              <th className="px-3 py-2 text-left">Product</th>
              <th className="px-3 py-2 text-left">Qty</th>
              <th className="px-3 py-2 text-left">Avg Price</th>
              <th className="px-3 py-2 text-left">Txn</th>
              <th className="px-3 py-2 text-left">Fill Time</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t) => (
              <tr key={t.trade_id} className="border-t border-slate-100">
                <td className="px-3 py-2 tabular-nums">{t.trade_id}</td>
                <td className="px-3 py-2 tabular-nums">{t.order_id}</td>
                <td className="px-3 py-2">{t.tradingsymbol}</td>
                <td className="px-3 py-2">{t.product}</td>
                <td className="px-3 py-2 tabular-nums">{t.quantity}</td>
                <td className="px-3 py-2 tabular-nums">{t.average_price?.toFixed?.(2) ?? t.average_price}</td>
                <td className="px-3 py-2">{t.transaction_type}</td>
                <td className="px-3 py-2 text-slate-600">{formatTime(t.fill_timestamp)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
