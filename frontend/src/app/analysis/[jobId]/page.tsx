"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { analysisApi, reportsApi } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import { useJobStream } from "@/lib/useJobStream";
import { PipelineProgress } from "@/components/PipelineProgress";
import { ChartGrid } from "@/components/ChartGrid";
import { ModelTable } from "@/components/ModelTable";
import { ChatPanel } from "@/components/ChatPanel";
import { ReportPanel } from "@/components/ReportPanel";
import { ColumnTable } from "@/components/ColumnTable";
import { AnomalyCard } from "@/components/AnomalyCard";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

const TABS = ["Overview", "Charts", "Models", "Report", "Chat"] as const;
type Tab = typeof TABS[number];

export default function AnalysisPage() {
  const { jobId } = useParams() as { jobId: string };
  const router = useRouter();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<Tab>("Overview");

  useEffect(() => {
    if (!isAuthenticated()) router.replace("/login");
  }, [router]);

  // SSE live stream for pipeline progress
  const streamStatus = useJobStream(jobId);

  // Fallback polling (also used when SSE completes)
  const { data: polledStatus } = useQuery({
    queryKey: ["job-status", jobId],
    queryFn: () => analysisApi.status(jobId).then((r) => r.data),
    refetchInterval: streamStatus?.status === "completed" ? false : 5000,
    enabled: !!jobId,
  });

  // Prefer live stream, fallback to polled
  const status = streamStatus ?? polledStatus;

  // Invalidate result queries once job completes
  useEffect(() => {
    if (status?.status === "completed") {
      queryClient.invalidateQueries({ queryKey: ["job-results", jobId] });
      queryClient.invalidateQueries({ queryKey: ["job-charts", jobId] });
      queryClient.invalidateQueries({ queryKey: ["job-models", jobId] });
      queryClient.invalidateQueries({ queryKey: ["job-report", jobId] });
    }
  }, [status?.status, jobId, queryClient]);

  const { data: results } = useQuery({
    queryKey: ["job-results", jobId],
    queryFn: () => analysisApi.results(jobId).then((r) => r.data),
    enabled: status?.status === "completed",
  });

  const { data: charts } = useQuery({
    queryKey: ["job-charts", jobId],
    queryFn: () => analysisApi.charts(jobId).then((r) => r.data),
    enabled: status?.status === "completed",
  });

  const { data: models } = useQuery({
    queryKey: ["job-models", jobId],
    queryFn: () => analysisApi.models(jobId).then((r) => r.data),
    enabled: status?.status === "completed",
  });

  const { data: report } = useQuery({
    queryKey: ["job-report", jobId],
    queryFn: () => reportsApi.get(jobId).then((r) => r.data),
    enabled: status?.status === "completed",
  });

  const profile = results?.find((r: any) => r.type === "profile")?.data;
  const eda = results?.find((r: any) => r.type === "eda")?.data;
  const findings = results?.find((r: any) => r.type === "findings")?.data?.text;

  const statusColor =
    status?.status === "completed" ? "bg-green-100 text-green-700" :
    status?.status === "failed"    ? "bg-red-100 text-red-700" :
                                     "bg-yellow-100 text-yellow-700";

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-4">
        <Link href="/dashboard" className="text-gray-500 hover:text-gray-900 transition">
          <ArrowLeft size={20} />
        </Link>
        <div>
          <span className="font-bold text-gray-900">Analysis Job</span>
          <span className="text-xs text-gray-400 font-mono ml-2">#{jobId?.slice(0, 8)}</span>
        </div>
        {status && (
          <span className={`ml-auto text-xs font-semibold px-2.5 py-1 rounded-full ${statusColor}`}>
            {status.status}
          </span>
        )}
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-6">

        {/* Live progress */}
        {status && (status.status === "running" || status.status === "pending") && (
          <div className="mb-6">
            <PipelineProgress
              stage={status.current_stage}
              progress={status.progress}
            />
          </div>
        )}

        {/* Error banner */}
        {status?.status === "failed" && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 text-red-700 text-sm">
            <strong>Pipeline failed:</strong> {status.error_message}
          </div>
        )}

        {/* Pending placeholder */}
        {status?.status === "pending" && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-8 text-center text-blue-600 mb-6">
            <div className="text-3xl mb-2">⏳</div>
            <p className="font-medium">Analysis queued — waiting for a worker to pick it up…</p>
          </div>
        )}

        {/* Completed content */}
        {status?.status === "completed" && (
          <>
            {/* Tab bar */}
            <div className="flex gap-1 bg-white border border-gray-200 rounded-xl p-1 mb-6 w-fit">
              {TABS.map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                    activeTab === tab
                      ? "bg-brand-600 text-white shadow-sm"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Tab content */}
            {activeTab === "Overview" && (
              <div className="space-y-6">
                {profile && <ProfileCard profile={profile} eda={eda} />}
                {profile?.columns && <ColumnTable columns={profile.columns} />}
                {results?.find((r: any) => r.type === "anomalies") && (
                  <AnomalyCard anomalies={results.find((r: any) => r.type === "anomalies")?.data} />
                )}
                {findings && (
                  <div className="bg-white rounded-xl border border-gray-200 p-6">
                    <h3 className="font-semibold text-gray-900 mb-3">🔍 AI Key Findings</h3>
                    <p className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">
                      {findings}
                    </p>
                  </div>
                )}
                {results?.find((r: any) => r.type === "feature_recommendations") && (
                  <div className="bg-white rounded-xl border border-gray-200 p-6">
                    <h3 className="font-semibold text-gray-900 mb-3">🎯 Feature Recommendations</h3>
                    <p className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">
                      {results.find((r: any) => r.type === "feature_recommendations")?.data?.text}
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === "Charts" && <ChartGrid charts={charts ?? []} />}
            {activeTab === "Models" && <ModelTable models={models ?? []} />}
            {activeTab === "Report" && <ReportPanel report={report} jobId={jobId} />}
            {activeTab === "Chat"   && <ChatPanel jobId={jobId} />}
          </>
        )}
      </div>
    </div>
  );
}

function ProfileCard({ profile, eda }: { profile: any; eda: any }) {
  const stats = [
    { label: "Rows",            value: profile.shape?.rows?.toLocaleString() },
    { label: "Columns",         value: profile.shape?.cols },
    { label: "Task Type",       value: eda?.task_type ?? "N/A" },
    { label: "Target Column",   value: eda?.target_candidate ?? "N/A" },
    { label: "Duplicate Rows",  value: profile.duplicate_rows },
    { label: "Memory",          value: `${profile.memory_mb} MB` },
    { label: "Skewed Columns",  value: eda?.skewed_columns?.length ?? 0 },
    { label: "High Cardinality",value: eda?.high_cardinality_columns?.length ?? 0 },
  ];

  const nullyCols = profile.columns?.filter((c: any) => c.null_pct > 5) ?? [];

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="font-semibold text-gray-900 mb-4">📊 Dataset Overview</h3>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        {stats.map((item) => (
          <div key={item.label} className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-500">{item.label}</div>
            <div className="font-semibold text-gray-900 mt-0.5 truncate">{item.value}</div>
          </div>
        ))}
      </div>

      {nullyCols.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-medium text-gray-600 mb-2">Columns with significant nulls (&gt;5%):</p>
          <div className="flex flex-wrap gap-2">
            {nullyCols.map((c: any) => (
              <span key={c.name} className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">
                {c.name} ({c.null_pct}%)
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
