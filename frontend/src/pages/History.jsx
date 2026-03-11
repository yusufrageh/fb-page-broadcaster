import { useState, useEffect } from "react";
import api from "../api/client";
import StatusBadge from "../components/StatusBadge";

export default function History() {
  const [broadcasts, setBroadcasts] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/history").then((r) => {
      setBroadcasts(r.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const viewDetail = async (id) => {
    setSelected(id);
    try {
      const r = await api.get(`/history/${id}`);
      setDetail(r.data);
    } catch {
      setDetail(null);
    }
  };

  const formatDate = (d) => d ? new Date(d).toLocaleString() : "-";

  return (
    <div className="max-w-4xl">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Broadcast History</h2>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : broadcasts.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border p-8 text-center text-gray-500">
          No broadcasts yet.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* List */}
          <div className="space-y-3">
            {broadcasts.map((b) => (
              <div
                key={b.id}
                onClick={() => viewDetail(b.id)}
                className={`bg-white rounded-xl shadow-sm border p-4 cursor-pointer hover:border-blue-300 transition-colors ${
                  selected === b.id ? "ring-2 ring-blue-500" : ""
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <StatusBadge status={b.status} />
                  <span className="text-xs text-gray-400">{formatDate(b.created_at)}</span>
                </div>
                <p className="text-sm text-gray-700 line-clamp-2 mb-2">{b.base_message}</p>
                <div className="flex gap-4 text-xs text-gray-500">
                  <span>Sent: {b.sent_count}</span>
                  <span>Failed: {b.failed_count}</span>
                  <span>Total: {b.total_contacts}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Detail */}
          {detail && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-800">Broadcast #{detail.id}</h3>
                <StatusBadge status={detail.status} />
              </div>

              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-gray-500">Base Message:</span>
                  <p className="text-gray-800 mt-1">{detail.base_message}</p>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-green-50 rounded-lg p-2">
                    <div className="text-lg font-bold text-green-700">{detail.sent_count}</div>
                    <div className="text-xs text-green-600">Sent</div>
                  </div>
                  <div className="bg-red-50 rounded-lg p-2">
                    <div className="text-lg font-bold text-red-700">{detail.failed_count}</div>
                    <div className="text-xs text-red-600">Failed</div>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-2">
                    <div className="text-lg font-bold text-blue-700">{detail.total_contacts}</div>
                    <div className="text-xs text-blue-600">Total</div>
                  </div>
                </div>
                <div className="text-xs text-gray-400">
                  Started: {formatDate(detail.created_at)} | Ended: {formatDate(detail.completed_at)}
                </div>
              </div>

              {detail.message_logs?.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Messages ({detail.message_logs.length})
                  </h4>
                  <div className="max-h-64 overflow-y-auto space-y-2">
                    {detail.message_logs.map((log) => (
                      <div key={log.id} className="border rounded-lg p-3 text-xs">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-gray-700">{log.contact_name}</span>
                          <StatusBadge status={log.status} />
                        </div>
                        <p className="text-gray-600">{log.message_text}</p>
                        {log.error_message && (
                          <p className="text-red-500 mt-1">{log.error_message}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
