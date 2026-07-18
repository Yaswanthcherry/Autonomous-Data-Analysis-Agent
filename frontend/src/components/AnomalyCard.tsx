"use client";

interface IQRInfo {
  count: number;
  pct: number;
  lower_bound: number;
  upper_bound: number;
}

interface IsolationForest {
  count: number;
  pct: number;
}

interface AnomalyData {
  iqr?: Record<string, IQRInfo>;
  zscore?: Record<string, { count: number; pct: number }>;
  isolation_forest?: IsolationForest;
}

export function AnomalyCard({ anomalies }: { anomalies: AnomalyData }) {
  if (!anomalies || anomalies.method === "none") {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 text-center text-gray-400 text-sm">
        No numeric columns found for anomaly detection.
      </div>
    );
  }

  const iqrEntries = Object.entries(anomalies.iqr ?? {})
    .filter(([, v]) => v.count > 0)
    .sort((a, b) => b[1].pct - a[1].pct)
    .slice(0, 8);

  const ifResult = anomalies.isolation_forest;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="font-semibold text-gray-900 mb-4">🔎 Anomaly Detection</h3>

      {/* Isolation Forest summary */}
      {ifResult && (
        <div className={`rounded-lg px-4 py-3 mb-4 flex items-center justify-between ${
          ifResult.count === 0 ? "bg-green-50 text-green-700" : "bg-orange-50 text-orange-700"
        }`}>
          <span className="text-sm font-medium">Isolation Forest anomalies</span>
          <span className="font-bold text-lg">{ifResult.count}
            <span className="text-xs font-normal ml-1">({ifResult.pct}%)</span>
          </span>
        </div>
      )}

      {/* IQR outliers per column */}
      {iqrEntries.length > 0 && (
        <>
          <p className="text-xs text-gray-500 font-medium mb-2 uppercase tracking-wide">
            IQR Outliers by Column
          </p>
          <div className="space-y-2">
            {iqrEntries.map(([col, info]) => (
              <div key={col} className="flex items-center gap-3">
                <span className="text-xs text-gray-700 w-36 truncate" title={col}>{col}</span>
                <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-red-400 rounded-full"
                    style={{ width: `${Math.min(info.pct * 5, 100)}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500 w-20 text-right tabular-nums">
                  {info.count} ({info.pct}%)
                </span>
              </div>
            ))}
          </div>
        </>
      )}

      {iqrEntries.length === 0 && ifResult?.count === 0 && (
        <p className="text-sm text-green-600 font-medium">✓ No significant outliers detected</p>
      )}
    </div>
  );
}
