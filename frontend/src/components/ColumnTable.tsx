"use client";
import { useState } from "react";

interface Column {
  name: string;
  dtype: string;
  kind: string;
  null_count: number;
  null_pct: number;
  unique_count: number;
  mean?: number;
  std?: number;
  min?: number;
  max?: number;
  median?: number;
  top_values?: Record<string, number>;
}

export function ColumnTable({ columns }: { columns: Column[] }) {
  const [filter, setFilter] = useState("");

  const filtered = columns.filter((c) =>
    c.name.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="p-5 border-b border-gray-100 flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">📋 Column Details</h3>
        <input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter columns…"
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-brand-500 w-44"
        />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="bg-gray-50 text-gray-600 uppercase tracking-wide">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Column</th>
              <th className="text-left px-4 py-3 font-medium">Type</th>
              <th className="text-right px-4 py-3 font-medium">Nulls</th>
              <th className="text-right px-4 py-3 font-medium">Unique</th>
              <th className="text-right px-4 py-3 font-medium">Mean / Top</th>
              <th className="text-right px-4 py-3 font-medium">Min–Max</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((col) => (
              <tr key={col.name} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900 max-w-[140px] truncate" title={col.name}>
                  {col.name}
                </td>
                <td className="px-4 py-3">
                  <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                    col.kind === "numeric"     ? "bg-blue-100 text-blue-700" :
                    col.kind === "categorical" ? "bg-purple-100 text-purple-700" :
                                                 "bg-green-100 text-green-700"
                  }`}>
                    {col.dtype}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  {col.null_count > 0 ? (
                    <span className="text-orange-600 font-medium">
                      {col.null_count} ({col.null_pct}%)
                    </span>
                  ) : (
                    <span className="text-green-600">0</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right text-gray-600">{col.unique_count}</td>
                <td className="px-4 py-3 text-right text-gray-600">
                  {col.kind === "numeric" && col.mean != null
                    ? col.mean.toFixed(2)
                    : col.top_values
                    ? Object.keys(col.top_values)[0] ?? "—"
                    : "—"}
                </td>
                <td className="px-4 py-3 text-right text-gray-600">
                  {col.kind === "numeric" && col.min != null && col.max != null
                    ? `${col.min.toFixed(1)} – ${col.max.toFixed(1)}`
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
