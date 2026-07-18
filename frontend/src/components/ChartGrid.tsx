"use client";
import dynamic from "next/dynamic";
import { useState } from "react";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface Chart {
  id: string;
  title: string;
  chart_type: string;
  plotly_json: any;
}

export function ChartGrid({ charts }: { charts: Chart[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (!charts.length) {
    return <div className="text-center py-12 text-gray-400">No charts available yet.</div>;
  }

  return (
    <>
      <div className="grid gap-6 sm:grid-cols-2">
        {charts.map((chart) => (
          <div
            key={chart.id}
            className="bg-white rounded-xl border border-gray-200 p-4 cursor-pointer hover:shadow-md transition"
            onClick={() => setExpanded(chart.id)}
          >
            <h4 className="text-sm font-semibold text-gray-800 mb-3">{chart.title}</h4>
            <Plot
              data={chart.plotly_json.data}
              layout={{
                ...chart.plotly_json.layout,
                height: 280,
                margin: { t: 20, r: 10, b: 40, l: 40 },
                autosize: true,
              }}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: "100%" }}
            />
          </div>
        ))}
      </div>

      {/* Expanded modal */}
      {expanded && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setExpanded(null)}
        >
          <div
            className="bg-white rounded-2xl p-6 max-w-4xl w-full max-h-[90vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {(() => {
              const chart = charts.find((c) => c.id === expanded)!;
              return (
                <>
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="font-semibold text-gray-900">{chart.title}</h3>
                    <button onClick={() => setExpanded(null)} className="text-gray-400 hover:text-gray-700 text-xl">✕</button>
                  </div>
                  <Plot
                    data={chart.plotly_json.data}
                    layout={{ ...chart.plotly_json.layout, height: 500, autosize: true }}
                    config={{ responsive: true }}
                    style={{ width: "100%" }}
                  />
                </>
              );
            })()}
          </div>
        </div>
      )}
    </>
  );
}
