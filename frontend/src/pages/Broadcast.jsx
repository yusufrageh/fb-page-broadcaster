import { useState, useEffect } from "react";
import api from "../api/client";
import useWebSocket from "../hooks/useWebSocket";
import ProgressBar from "../components/ProgressBar";
import StatusBadge from "../components/StatusBadge";

export default function Broadcast() {
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem("broadcast_message");
    if (saved) {
      localStorage.removeItem("broadcast_message");
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      } catch {}
      return saved.trim() ? [saved] : [""];
    }
    return [""];
  });
  const [batchSize, setBatchSize] = useState(50);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(null);
  const [logs, setLogs] = useState([]);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");
  const [resetting, setResetting] = useState(false);
  const [resetResult, setResetResult] = useState(null);
  const [stats, setStats] = useState(null);
  const [images, setImages] = useState([]);

  const { on, connected } = useWebSocket();

  useEffect(() => {
    api.get("/broadcast/status").then((r) => setStatus(r.data)).catch(() => {});
    api.get("/settings").then((r) => setBatchSize(r.data.default_batch_size)).catch(() => {});
    api.get("/broadcast/stats").then((r) => setStats(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    const unsub1 = on("broadcast:progress", (data) => setProgress(data));
    const unsub2 = on("broadcast:message_sent", (data) => setLogs((prev) => [data, ...prev]));
    const unsub3 = on("broadcast:completed", (data) => {
      setStatus((s) => ({ ...s, running: false, broadcast: { ...s?.broadcast, status: "completed" } }));
      setProgress(null);
      api.get("/broadcast/stats").then((r) => setStats(r.data)).catch(() => {});
    });
    const unsub4 = on("broadcast:error", (data) => setError(data.error_message));
    return () => { unsub1(); unsub2(); unsub3(); unsub4(); };
  }, [on]);

  const updateMessage = (index, value) => {
    setMessages((prev) => prev.map((m, i) => (i === index ? value : m)));
  };
  const addMessage = () => setMessages((prev) => [...prev, ""]);
  const removeMessage = (index) => setMessages((prev) => prev.filter((_, i) => i !== index));

  const hasValidMessage = messages.some((m) => m.trim());

  const handleImageUpload = async (e) => {
    const files = Array.from(e.target.files);
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      try {
        const r = await api.post("/broadcast/upload-image", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setImages((prev) => [
          ...prev,
          {
            filename: r.data.filename,
            originalName: r.data.original_name,
            previewUrl: `/uploads/${r.data.filename}`,
          },
        ]);
      } catch (err) {
        setError(err.response?.data?.detail || "Image upload failed");
      }
    }
    e.target.value = "";
  };

  const removeImage = async (filename) => {
    try {
      await api.delete(`/broadcast/upload-image/${filename}`);
      setImages((prev) => prev.filter((img) => img.filename !== filename));
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete image");
    }
  };

  const start = async () => {
    const validMessages = messages.filter((m) => m.trim());
    if (validMessages.length === 0) return;
    setStarting(true);
    setError("");
    setLogs([]);
    try {
      const r = await api.post("/broadcast/start", {
        messages: validMessages,
        batch_size: batchSize,
        image_filenames: images.map((img) => img.filename),
      });
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

  const resetCampaign = async () => {
    if (!confirm("Start a new campaign?\n\nThis will clear the sent-to history so ALL contacts will receive messages again.")) return;
    setResetting(true);
    setResetResult(null);
    try {
      const r = await api.post("/broadcast/reset-campaign");
      setResetResult(`Campaign reset — ${r.data.reset_count} contacts cleared for "${r.data.page_name}"`);
      api.get("/broadcast/stats").then((r) => setStats(r.data)).catch(() => {});
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
    setResetting(false);
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

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-sm border p-4 text-center">
            <div className="text-2xl font-bold text-green-700">{stats.total_sent_to}</div>
            <div className="text-xs text-gray-500 mt-1">Sent To (this campaign)</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border p-4 text-center">
            <div className="text-2xl font-bold text-blue-700">{stats.total_contacts}</div>
            <div className="text-xs text-gray-500 mt-1">Total Contacts in DB</div>
          </div>
        </div>
      )}

      {/* Compose & Launch */}
      {!isRunning && (
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-6 space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm font-medium text-gray-700">
                Messages ({messages.length} variant{messages.length > 1 ? "s" : ""})
              </label>
              <button
                type="button"
                onClick={addMessage}
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                + Add Variant
              </button>
            </div>
            <p className="text-xs text-gray-500 mb-2">Each contact will receive a randomly picked variant.</p>
            <div className="space-y-2">
              {messages.map((msg, i) => (
                <div key={i} className="flex gap-2">
                  <textarea
                    className="flex-1 border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
                    rows={3}
                    value={msg}
                    onChange={(e) => updateMessage(i, e.target.value)}
                    placeholder={`Message variant ${i + 1}...`}
                  />
                  {messages.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeMessage(i)}
                      className="text-red-400 hover:text-red-600 px-1 self-start mt-1"
                      title="Remove variant"
                    >
                      &times;
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
          {/* Image Attachments */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm font-medium text-gray-700">
                Images {images.length > 0 && `(${images.length})`}
              </label>
              <label className="text-blue-600 hover:text-blue-800 text-sm font-medium cursor-pointer">
                + Add Image
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  className="hidden"
                  onChange={handleImageUpload}
                />
              </label>
            </div>
            <p className="text-xs text-gray-500 mb-2">Optional — each contact gets a randomly picked image pasted into the chat.</p>
            {images.length > 0 && (
              <div className="flex flex-wrap gap-3">
                {images.map((img) => (
                  <div key={img.filename} className="relative group">
                    <img
                      src={img.previewUrl}
                      alt={img.originalName}
                      className="w-20 h-20 object-cover rounded-lg border"
                    />
                    <button
                      type="button"
                      onClick={() => removeImage(img.filename)}
                      className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Remove"
                    >
                      &times;
                    </button>
                    <p className="text-xs text-gray-400 mt-1 truncate w-20">{img.originalName}</p>
                  </div>
                ))}
              </div>
            )}
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
              disabled={starting || !hasValidMessage}
              className="bg-green-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {starting ? "Starting..." : "Start Broadcast"}
            </button>
            <button
              onClick={resetCampaign}
              disabled={resetting}
              className="bg-amber-500 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-amber-600 disabled:opacity-50 transition-colors"
            >
              {resetting ? "Resetting..." : "New Campaign"}
            </button>
          </div>
          {resetResult && (
            <p className="text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-sm">{resetResult}</p>
          )}
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
