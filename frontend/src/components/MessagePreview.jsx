export default function MessagePreview({ variants }) {
  if (!variants || variants.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-gray-700">
        AI-Generated Variants ({variants.length})
      </h3>
      {variants.map((v, i) => (
        <div key={i} className="bg-gray-50 border rounded-lg p-3">
          <div className="text-xs text-gray-400 mb-1">Variant {i + 1}</div>
          <p className="text-sm text-gray-800">{v}</p>
        </div>
      ))}
    </div>
  );
}
