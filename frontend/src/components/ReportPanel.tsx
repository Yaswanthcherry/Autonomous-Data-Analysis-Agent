"use client";
import { reportsApi } from "@/lib/api";
import { Download, FileText } from "lucide-react";

interface Report {
  executive_summary: string;
  business_insights: string;
  pdf_available: boolean;
  created_at: string;
}

export function ReportPanel({ report, jobId }: { report: Report | undefined; jobId: string }) {
  if (!report) {
    return <div className="text-center py-12 text-gray-400">Report not available yet.</div>;
  }

  return (
    <div className="space-y-6">
      {/* Download */}
      {report.pdf_available && (
        <div className="bg-gradient-to-r from-brand-900 to-brand-600 rounded-xl p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText size={28} className="text-white" />
            <div>
              <p className="font-semibold text-white">Full PDF Report</p>
              <p className="text-brand-200 text-sm">Complete analysis with charts and insights</p>
            </div>
          </div>
          <a
            href={reportsApi.downloadUrl(jobId)}
            download
            className="flex items-center gap-2 bg-white text-brand-700 font-semibold text-sm px-4 py-2 rounded-lg hover:bg-brand-50 transition"
          >
            <Download size={16} />
            Download PDF
          </a>
        </div>
      )}

      {/* Executive Summary */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">📋 Executive Summary</h3>
        <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
          {report.executive_summary}
        </p>
      </div>

      {/* Business Insights */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">💡 Business Insights</h3>
        <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
          {report.business_insights}
        </p>
      </div>
    </div>
  );
}
