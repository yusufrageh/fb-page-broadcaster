import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Compose() {
  const navigate = useNavigate();
  const [message, setMessage] = useState(() => localStorage.getItem("broadcast_message") || "");

  return (
    <div className="max-w-2xl">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Compose Message</h2>

      <div className="bg-white rounded-xl shadow-sm border p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Message
          </label>
          <textarea
            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
            rows={5}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your broadcast message here..."
          />
        </div>

        <button
          onClick={() => {
            localStorage.setItem("broadcast_message", JSON.stringify([message]));
            navigate("/broadcast");
          }}
          disabled={!message.trim()}
          className="bg-green-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
        >
          Use in Broadcast
        </button>
      </div>
    </div>
  );
}
