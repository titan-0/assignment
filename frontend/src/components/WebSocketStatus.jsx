export default function WebSocketStatus({ status }) {
  const color = status === 'connected' ? 'bg-green-500' : status === 'connecting' ? 'bg-yellow-500' : 'bg-red-500';
  const label = status === 'connected' ? 'Connected' : status === 'connecting' ? 'Connecting' : 'Disconnected';
  return (
    <div className="flex items-center gap-2">
      <span className={`inline-block h-3 w-3 rounded-full ${color}`}></span>
      <span className="text-sm text-slate-600">{label}</span>
    </div>
  );
}
