"use client";

const STAGES = [
  { key: "profiling", label: "Profiling" },
  { key: "cleaning", label: "Cleaning" },
  { key: "anomaly_detection", label: "Anomalies" },
  { key: "eda", label: "EDA" },
  { key: "chart_generation", label: "Charts" },
  { key: "ai_findings", label: "AI Findings" },
  { key: "feature_recommendations", label: "Features" },
  { key: "model_training", label: "Training" },
  { key: "model_comparison", label: "Comparing" },
  { key: "business_insights", label: "Insights" },
  { key: "executive_summary", label: "Summary" },
  { key: "pdf_export", label: "PDF" },
  { key: "complete", label: "Done" },
];

interface Props {
  stage: string | null;
  progress: number;
}

export function PipelineProgress({ stage, progress }: Props) {
  const currentIdx = STAGES.findIndex((s) => s.key === stage);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">🔄 Analysis in Progress</h3>
        <span className="text-sm font-medium text-brand-600">{progress}%</span>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-gray-100 rounded-full mb-6 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-brand-500 to-brand-600 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Stage indicators */}
      <div className="flex flex-wrap gap-2">
        {STAGES.map((s, i) => {
          const isActive = s.key === stage;
          const isDone = i < currentIdx;
          return (
            <span
              key={s.key}
              className={`text-xs px-2 py-1 rounded-full font-medium transition ${
                isActive
                  ? "bg-brand-100 text-brand-700 ring-1 ring-brand-400"
                  : isDone
                  ? "bg-green-100 text-green-700"
                  : "bg-gray-100 text-gray-400"
              }`}
            >
              {isDone ? "✓ " : isActive ? "⟳ " : ""}{s.label}
            </span>
          );
        })}
      </div>
    </div>
  );
}
