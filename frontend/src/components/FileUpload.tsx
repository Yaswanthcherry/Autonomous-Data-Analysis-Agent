"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { datasetsApi, analysisApi } from "@/lib/api";
import { toast } from "sonner";
import { Upload, FileText } from "lucide-react";
import { useRouter } from "next/navigation";

interface Props {
  onSuccess?: () => void;
}

export function FileUpload({ onSuccess }: Props) {
  const router = useRouter();
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      setUploading(true);
      setProgress(10);
      try {
        const uploadRes = await datasetsApi.upload(file);
        const datasetId = uploadRes.data.id;
        setProgress(40);

        const analysisRes = await analysisApi.start(datasetId);
        const jobId = analysisRes.data.job_id;
        setProgress(100);

        toast.success("Analysis started!");
        onSuccess?.();
        router.push(`/analysis/${jobId}`);
      } catch (err: any) {
        toast.error(err.response?.data?.detail || "Upload failed");
      } finally {
        setUploading(false);
        setProgress(0);
      }
    },
    [router, onSuccess]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/json": [".json"],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition
        ${isDragActive ? "border-brand-500 bg-brand-50" : "border-gray-300 hover:border-brand-400"}
        ${uploading ? "opacity-60 pointer-events-none" : ""}
      `}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-3">
        {uploading ? (
          <>
            <div className="w-12 h-12 rounded-full border-4 border-brand-200 border-t-brand-600 animate-spin" />
            <p className="text-sm text-gray-600">Uploading and starting analysis… {progress}%</p>
          </>
        ) : (
          <>
            <Upload size={36} className="text-gray-400" />
            <div>
              <p className="font-medium text-gray-700">
                {isDragActive ? "Drop your file here" : "Drag & drop or click to upload"}
              </p>
              <p className="text-xs text-gray-400 mt-1">CSV, XLSX, JSON — max 100MB</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
