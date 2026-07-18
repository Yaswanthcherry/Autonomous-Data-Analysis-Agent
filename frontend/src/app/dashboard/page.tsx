"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { datasetsApi } from "@/lib/api";
import { isAuthenticated, clearTokens } from "@/lib/auth";
import { FileUpload } from "@/components/FileUpload";
import { DatasetCard } from "@/components/DatasetCard";
import { formatBytes, formatDate } from "@/lib/utils";
import { LogOut, Database, BarChart3 } from "lucide-react";
import { toast } from "sonner";

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) router.replace("/login");
  }, [router]);

  const { data: datasets, refetch, isLoading } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => datasetsApi.list().then((r) => r.data),
    refetchInterval: 10000,
  });

  const handleLogout = () => {
    clearTokens();
    router.push("/login");
  };

  const handleUploadSuccess = () => {
    toast.success("Dataset uploaded! Starting analysis…");
    refetch();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🤖</span>
          <span className="font-bold text-gray-900 text-lg">AI Data Analyst</span>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-red-500 transition"
        >
          <LogOut size={16} />
          Logout
        </button>
      </nav>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          {[
            { icon: <Database size={20} />, label: "Datasets", value: datasets?.length ?? 0 },
            { icon: <BarChart3 size={20} />, label: "Analyses Run",
              value: datasets?.filter((d: any) => d.status === "analyzed").length ?? 0 },
            { icon: <span className="text-lg">📊</span>, label: "Total Rows",
              value: datasets?.reduce((s: number, d: any) => s + (d.row_count || 0), 0)?.toLocaleString() ?? 0 },
          ].map((stat, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4">
              <div className="text-brand-600">{stat.icon}</div>
              <div>
                <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                <div className="text-sm text-gray-500">{stat.label}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Upload */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Dataset</h2>
          <FileUpload onSuccess={handleUploadSuccess} />
        </div>

        {/* Dataset List */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Your Datasets</h2>
          {isLoading ? (
            <div className="text-center py-12 text-gray-400">Loading…</div>
          ) : datasets?.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              No datasets yet. Upload one above to get started.
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {datasets?.map((d: any) => (
                <DatasetCard key={d.id} dataset={d} onDeleted={refetch} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
