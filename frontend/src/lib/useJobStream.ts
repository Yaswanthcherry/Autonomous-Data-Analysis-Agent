"use client";
import { useEffect, useState, useRef } from "react";

interface JobStatus {
  job_id: string;
  status: string;
  current_stage: string | null;
  progress: number;
  error_message: string | null;
}

export function useJobStream(jobId: string | null) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const token = localStorage.getItem("access_token");
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    // SSE with token in query param (EventSource doesn't support headers)
    const url = `${API_URL}/api/v1/events/${jobId}/stream?token=${token}`;

    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (event) => {
      const data: JobStatus = JSON.parse(event.data);
      setStatus(data);
      if (data.status === "completed" || data.status === "failed") {
        es.close();
      }
    };

    es.onerror = () => {
      es.close();
    };

    return () => {
      es.close();
    };
  }, [jobId]);

  return status;
}
