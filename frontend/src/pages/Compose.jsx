import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import MessagePreview from "../components/MessagePreview";

export default function Compose() {
  const navigate = useNavigate();
  const [message, setMessage] = useState(() => localStorage.getItem("broadcast_message") || "");
  const [variantCount, setVariantCount] = useState(3);
  const [variants, setVariants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const preview = async () => {
    if (!message.trim()) return;
    setLoading(true);
    setError("");
    setVariants([]);
    try {
      const r = await api.post("/compose/preview", {
        base_message: message,
        variant_count: variantCount,
      });
      setVariants(r.data.variants);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
    setLoading(false);
  };

  return (
    <div className="max-w-2xl">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Compose Message</h2>

      <div className="bg-white rounded-xl shadow-sm border p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Base Message
          </label>
          <textarea
            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
            rows={5}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message here. Each recipient will get a unique AI-rephrased version."
          />
        </div>

        <div className="flex items-end gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Preview Variants
            </label>
            <input
              type="number"
              className="w-24 border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              value={variantCount}
              onChange={(e) => setVariantCount(Math.min(10, Math.max(1, +e.target.value)))}
              min={1}
              max={10}
            />
          </div>
          <button
            onClick={preview}
            disabled={loading || !message.trim()}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "Generating..." : "Generate Previews"}
          </button>
        </div>

        {error && <p className="text-red-600 text-sm">{error}</p>}
      </div>

      {variants.length > 0 && (
        <div className="mt-6 bg-white rounded-xl shadow-sm border p-6">
          <MessagePreview variants={variants} />
          <button
            onClick={() => {
              localStorage.setItem("broadcast_message", message);
              navigate("/broadcast");
            }}
            className="mt-4 bg-green-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
          >
            Use in Broadcast
          </button>
        </div>
      )}
    </div>
  );
}
