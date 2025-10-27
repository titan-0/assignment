import { formatTime } from '../lib/api';

const statusClasses = {
  FILLED: 'bg-green-100 text-green-800',
  OPEN: 'bg-emerald-100 text-emerald-800',
  PENDING: 'bg-yellow-100 text-yellow-800',
  CANCELLED: 'bg-red-100 text-red-800',
  FAILED: 'bg-red-100 text-red-800',
};

export default function OrdersTable({ orders, onRefresh, lastHighlightId }) {
  return (
    <div className="bg-white rounded-md border border-slate-200 shadow-sm">
      <div className="p-3 flex items-center justify-between">
        <h3 className="font-semibold text-slate-700">Live Orders</h3>
        <button onClick={onRefresh} className="px-3 py-1.5 text-sm rounded-md bg-slate-800 text-white hover:bg-slate-700">Refresh</button>
      </div>
      <div className="overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-3 py-2 text-left">Order ID</th>
              <th className="px-3 py-2 text-left">Ticker</th>
              <th className="px-3 py-2 text-left">Action</th>
              <th className="px-3 py-2 text-left">Qty</th>
              <th className="px-3 py-2 text-left">Price</th>
              <th className="px-3 py-2 text-left">Entry Status</th>
              <th className="px-3 py-2 text-left">Exit Status</th>
              <th className="px-3 py-2 text-left">Last Updated</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => {
              const highlight = lastHighlightId === o.order_id ? 'animate-pulse ring-2 ring-indigo-300' : '';
              return (
                <tr key={o.order_id} className={`border-t border-slate-100 ${highlight}`}>
                  <td className="px-3 py-2 tabular-nums">{o.order_id}</td>
                  <td className="px-3 py-2">{o.ticker}</td>
                  <td className="px-3 py-2">{o.action}</td>
                  <td className="px-3 py-2 tabular-nums">{o.quantity}</td>
                  <td className="px-3 py-2 tabular-nums">{o.price?.toFixed?.(2) ?? o.price}</td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${statusClasses[o.entry_status] || 'bg-slate-100 text-slate-700'}`}>
                      {o.entry_status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-slate-600">{o.exit_status || '—'}</td>
                  <td className="px-3 py-2 text-slate-600">{formatTime(o.last_updated)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
