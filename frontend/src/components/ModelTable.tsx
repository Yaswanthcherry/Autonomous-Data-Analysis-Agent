"use client";

interface Model {
  id: string;
  model_name: string;
  task_type: string;
  metrics: Record<string, number>;
  is_best: boolean;
  feature_importance: Record<string, number> | null;
}

export function ModelTable({ models }: { models: Model[] }) {
  if (!models.length) {
    return <div className="text-center py-12 text-gray-400">No models trained yet.</div>;
  }

  const taskType = models[0]?.task_type;
  const metricKeys = taskType === "classification"
    ? ["accuracy", "f1", "roc_auc"]
    : ["rmse", "mae", "r2"];

  const bestModel = models.find((m) => m.is_best);
  const topFeatures = bestModel?.feature_importance
    ? Object.entries(bestModel.feature_importance).slice(0, 10)
    : [];

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="p-5 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900">🏆 Model Comparison</h3>
          <p className="text-xs text-gray-500 mt-1">Task: {taskType}</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-5 py-3 font-medium text-gray-600">Model</th>
                {metricKeys.map((k) => (
                  <th key={k} className="text-right px-5 py-3 font-medium text-gray-600 uppercase text-xs">
                    {k}
                  </th>
                ))}
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {models.map((m) => (
                <tr key={m.id} className={m.is_best ? "bg-green-50" : "hover:bg-gray-50"}>
                  <td className="px-5 py-3 font-medium text-gray-900">{m.model_name}</td>
                  {metricKeys.map((k) => (
                    <td key={k} className="px-5 py-3 text-right tabular-nums text-gray-700">
                      {m.metrics[k] != null ? m.metrics[k].toFixed(4) : "—"}
                    </td>
                  ))}
                  <td className="px-5 py-3 text-right">
                    {m.is_best && (
                      <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-0.5 rounded-full">
                        Best ✓
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {topFeatures.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">🔑 Top Feature Importances ({bestModel?.model_name})</h3>
          <div className="space-y-2">
            {topFeatures.map(([feat, score]) => {
              const max = topFeatures[0][1];
              const pct = max > 0 ? (score / max) * 100 : 0;
              return (
                <div key={feat} className="flex items-center gap-3">
                  <span className="text-xs text-gray-600 w-40 truncate" title={feat}>{feat}</span>
                  <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-brand-500 rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-16 text-right tabular-nums">
                    {score.toFixed(4)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
