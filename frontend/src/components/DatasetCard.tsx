"use client";
import { useRouter } from "next/navigation";
import { datasetsApi, analysisApi } from "@/lib/api";
import { formatBytes, formatDate } from "@/lib/utils";
import { Trash2, BarChart3, FileText } from "lucide-react";
import { toast } from "sonner";
import { useState } from "react";

interface Dataset {
  id: string;
  original_name: string;
  file_type: string;
  file_size: number;
  status: string;
  row_count: number | null;
  col_count: number | null;
  created_at: string;
}

export function DatasetCard({ dataset, onDeleted }: { dataset: Dataset; onDeleted: () => void }) {
  const router = useRouter();
  const [deleting, setDeleting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Delete this dataset?")) return;
    setDeleting(true);
    try {
      await datasetsApi.delete(dataset.id);
      toast.success("Dataset deleted");
      onDeleted();
    } catch {
      toast.error("Delete failed");
    } finally {
      setDeleting(false);
    }
  };

  const handleAnalyze = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setAnalyzing(true);
    try {
      const res = await analysisApi.start(dataset.id);
      router.push(`/analysis/${res.data.job_id}`);
    } catch {
      toast.error("Failed to start analysis");
      setAnalyzing(false);
    }
  };

  const typeColors: Record<string, string> = {
    csv: "bg-green-100 text-green-700",
    xlsx: "bg-blue-100 text-blue-700",
    json: "bg-orange-100 text-orange-700",
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileText size={18} className="text-gray-400" />
          <span className={`text-xs font-bold px-2 py-0.5 rounded-full uppercase ${typeColors[dataset.file_type] ?? "bg-gray-100 text-gray-600"}`}>
            {dataset.file_type}
          </span>
        </div>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="text-gray-400 hover:text-red-500 transition"
          aria-label="Delete dataset"
        >
          <Trash2 size={16} />
        </button>
      </div>

      <p className="font-medium text-gray-900 text-sm truncate mb-1" title={dataset.original_name}>
        {dataset.original_name}
      </p>
      <p className="text-xs text-gray-400 mb-3">{formatBytes(dataset.file_size)}</p>

      {dataset.row_count && (
        <p className="text-xs text-gray-500 mb-3">
          {dataset.row_count.toLocaleString()} rows × {dataset.col_count} cols
        </p>
      )}

      <p className="text-xs text-gray-400 mb-4">{formatDate(dataset.created_at)}</p>

      <button
        onClick={handleAnalyze}
        disabled={analyzing}
        className="w-full flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium py-2 rounded-lg transition disabled:opacity-60"
      >
        <BarChart3 size={14} />
        {analyzing ? "Starting…" : "Analyze"}
      </button>
    </div>
  );
}
