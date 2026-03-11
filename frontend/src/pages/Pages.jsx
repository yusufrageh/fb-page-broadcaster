import { useState, useEffect } from "react";
import api from "../api/client";

export default function Pages() {
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState("");

  const loadPages = async () => {
    setLoading(true);
    try {
      const r = await api.get("/pages");
      setPages(r.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadPages();
  }, []);

  const fetchFromFB = async () => {
    setFetching(true);
    setError("");
    try {
      const r = await api.post("/pages/fetch");
      setPages(r.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
    setFetching(false);
  };

  const activate = async (id) => {
    try {
      await api.put(`/pages/${id}/activate`);
      await loadPages();
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Facebook Pages</h2>
        <button
          onClick={fetchFromFB}
          disabled={fetching}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {fetching ? "Fetching..." : "Fetch from Facebook"}
        </button>
      </div>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : pages.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border p-8 text-center text-gray-500">
          No pages found. Click "Fetch from Facebook" to import your pages.
        </div>
      ) : (
        <div className="space-y-3">
          {pages.map((page) => (
            <div
              key={page.id}
              className={`bg-white rounded-xl shadow-sm border p-4 flex items-center justify-between ${
                page.is_active ? "ring-2 ring-blue-500" : ""
              }`}
            >
              <div>
                <h3 className="font-semibold text-gray-900">{page.name}</h3>
                <p className="text-xs text-gray-400">ID: {page.fb_page_id}</p>
              </div>
              <div className="flex items-center gap-3">
                {page.is_active ? (
                  <span className="text-sm text-green-600 font-medium">Active</span>
                ) : (
                  <button
                    onClick={() => activate(page.id)}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Set Active
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
