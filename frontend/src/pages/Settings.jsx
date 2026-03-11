import { useState, useEffect } from "react";
import api from "../api/client";

export default function Settings() {
  const [form, setForm] = useState({
    fb_email: "",
    fb_password: "",
    gemini_api_key: "",
    min_delay: 5,
    max_delay: 15,
    default_batch_size: 50,
    max_contacts: 100,
  });
  const [status, setStatus] = useState({ fb_password_set: false, gemini_api_key_set: false });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.get("/settings").then((r) => {
      setStatus({ fb_password_set: r.data.fb_password_set, gemini_api_key_set: r.data.gemini_api_key_set });
      setForm((f) => ({
        ...f,
        fb_email: r.data.fb_email,
        min_delay: r.data.min_delay,
        max_delay: r.data.max_delay,
        default_batch_size: r.data.default_batch_size,
        max_contacts: r.data.max_contacts,
      }));
    });
  }, []);

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMsg("");
    try {
      const payload = { ...form };
      if (!payload.fb_password) delete payload.fb_password;
      if (!payload.gemini_api_key) delete payload.gemini_api_key;
      const r = await api.put("/settings", payload);
      setStatus({ fb_password_set: r.data.fb_password_set, gemini_api_key_set: r.data.gemini_api_key_set });
      setMsg("Settings saved!");
      setForm((f) => ({ ...f, fb_password: "", gemini_api_key: "" }));
    } catch (err) {
      setMsg("Error: " + (err.response?.data?.detail || err.message));
    }
    setSaving(false);
  };

  return (
    <div className="max-w-2xl">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Settings</h2>
      <form onSubmit={save} className="space-y-6">
        <div className="bg-white rounded-xl shadow-sm border p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-800">Facebook Credentials</h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              value={form.fb_email}
              onChange={(e) => setForm({ ...form, fb_email: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password {status.fb_password_set && <span className="text-green-600">(set)</span>}
            </label>
            <input
              type="password"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              value={form.fb_password}
              onChange={(e) => setForm({ ...form, fb_password: e.target.value })}
              placeholder={status.fb_password_set ? "Leave blank to keep current" : "Enter password"}
            />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-800">Gemini API</h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              API Key {status.gemini_api_key_set && <span className="text-green-600">(set)</span>}
            </label>
            <input
              type="password"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              value={form.gemini_api_key}
              onChange={(e) => setForm({ ...form, gemini_api_key: e.target.value })}
              placeholder={status.gemini_api_key_set ? "Leave blank to keep current" : "Enter Gemini API key"}
            />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-800">Broadcast Defaults</h3>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Min Delay (s)</label>
              <input
                type="number"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={form.min_delay}
                onChange={(e) => setForm({ ...form, min_delay: +e.target.value })}
                min={1}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max Delay (s)</label>
              <input
                type="number"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={form.max_delay}
                onChange={(e) => setForm({ ...form, max_delay: +e.target.value })}
                min={1}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Batch Size</label>
              <input
                type="number"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={form.default_batch_size}
                onChange={(e) => setForm({ ...form, default_batch_size: +e.target.value })}
                min={1}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max Contacts</label>
              <input
                type="number"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={form.max_contacts}
                onChange={(e) => setForm({ ...form, max_contacts: +e.target.value })}
                min={1}
              />
            </div>
          </div>
        </div>

        {msg && (
          <p className={`text-sm ${msg.startsWith("Error") ? "text-red-600" : "text-green-600"}`}>
            {msg}
          </p>
        )}

        <button
          type="submit"
          disabled={saving}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {saving ? "Saving..." : "Save Settings"}
        </button>
      </form>
    </div>
  );
}
