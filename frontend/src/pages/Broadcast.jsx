import { useState, useEffect } from "react";
import api from "../api/client";
import useWebSocket from "../hooks/useWebSocket";
import ProgressBar from "../components/ProgressBar";
import StatusBadge from "../components/StatusBadge";

export default function Broadcast() {
  const [message, setMessage] = useState(() => {
    const saved = localStorage.getItem("broadcast_message");
    if (saved) localStorage.removeItem("broadcast_message");
    return saved || "";
  });
  const [batchSize, setBatchSize] = useState(50);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(null);
  const [logs, setLogs] = useState([]);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");

  const { on, connected } = useWebSocket();

  useEffect(() => {
    api.get("/broadcast/status").then((r) => setStatus(r.data)).catch(() => {});
    api.get("/settings").then((r) => setBatchSize(r.data.default_batch_size)).catch(() => {});
  }, []);

  useEffect(() => {
    const unsub1 = on("broadcast:progress", (data) => setProgress(data));
    const unsub2 = on("broadcast:message_sent", (data) => setLogs((prev) => [data, ...prev]));
    const unsub3 = on("broadcast:completed", (data) => {
      setStatus((s) => ({ ...s, running: false, broadcast: { ...s?.broadcast, status: "completed" } }));
      setProgress(null);
    });
    const unsub4 = on("broadcast:error", (data) => setError(data.error_message));
    return () => { unsub1(); unsub2(); unsub3(); unsub4(); };
  }, [on]);

  const start = async () => {
    if (!message.trim()) return;
    setStarting(true);
    setError("");
    setLogs([]);
    try {
      const r = await api.post("/broadcast/start", { base_message: message, batch_size: batchSize });
      setStatus({ running: true, broadcast: r.data });
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
    setStarting(false);
  };

  const stop = async () => {
    try {
      await api.post("/broadcast/stop");
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  const isRunning = status?.running;

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Broadcast</h2>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connected ? "bg-green-500" : "bg-red-500"}`} />
          <span className="text-xs text-gray-500">{connected ? "Connected" : "Disconnected"}</span>
        </div>
      </div>

      {/* Compose & Launch */}
      {!isRunning && (
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
            <textarea
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
              rows={4}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your broadcast message..."
            />
          </div>
          <div className="flex items-end gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Batch Size</label>
              <input
                type="number"
                className="w-24 border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={batchSize}
                onChange={(e) => setBatchSize(+e.target.value)}
                min={1}
              />
            </div>
            <button
              onClick={start}
              disabled={starting || !message.trim()}
              className="bg-green-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {starting ? "Starting..." : "Start Broadcast"}
            </button>
          </div>
        </div>
      )}

      {/* Running status */}
      {isRunning && (
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <StatusBadge status="running" />
              {progress?.current_contact && (
                <span className="text-sm text-gray-600">
                  Sending to: {progress.current_contact}
                </span>
              )}
            </div>
            <button
              onClick={stop}
              className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700 transition-colors"
            >
              Stop
            </button>
          </div>

          {progress && (
            <div className="space-y-2">
              <ProgressBar
                value={progress.sent + progress.failed}
                max={progress.total}
                label={`${progress.sent} sent, ${progress.failed} failed, ${progress.remaining} remaining`}
              />
            </div>
          )}
        </div>
      )}

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {/* Live log */}
      {logs.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Live Log</h3>
          <div className="max-h-64 overflow-y-auto space-y-2">
            {logs.map((log, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <StatusBadge status={log.status} />
                <span className="font-medium text-gray-700">{log.contact_name}</span>
                <span className="text-gray-400 truncate flex-1">{log.message_preview}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
