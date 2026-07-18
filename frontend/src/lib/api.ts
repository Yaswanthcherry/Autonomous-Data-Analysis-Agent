import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token from localStorage
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refresh = localStorage.getItem("refresh_token");
        const { data } = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
          refresh_token: refresh,
        });
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch {
        localStorage.clear();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth ──
export const authApi = {
  register: (data: { email: string; full_name: string; password: string }) =>
    api.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),
  me: () => api.get("/auth/me"),
};

// ── Datasets ──
export const datasetsApi = {
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/datasets/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  list: () => api.get("/datasets/"),
  get: (id: string) => api.get(`/datasets/${id}`),
  delete: (id: string) => api.delete(`/datasets/${id}`),
};

// ── Analysis ──
export const analysisApi = {
  start: (datasetId: string) => api.post(`/analysis/${datasetId}/start`),
  status: (jobId: string) => api.get(`/analysis/${jobId}/status`),
  results: (jobId: string) => api.get(`/analysis/${jobId}/results`),
  charts: (jobId: string) => api.get(`/analysis/${jobId}/charts`),
  models: (jobId: string) => api.get(`/analysis/${jobId}/models`),
};

// ── Chat ──
export const chatApi = {
  send: (jobId: string, message: string) =>
    api.post(`/chat/${jobId}/message`, { message }),
  history: (jobId: string) => api.get(`/chat/${jobId}/history`),
};

// ── Reports ──
export const reportsApi = {
  get: (jobId: string) => api.get(`/reports/${jobId}`),
  downloadUrl: (jobId: string) =>
    `${API_URL}/api/v1/reports/${jobId}/download`,
};

// ── Users ──
export const usersApi = {
  me: () => api.get("/users/me"),
  updateMe: (data: { full_name?: string; password?: string }) =>
    api.patch("/users/me", data),
  list: () => api.get("/users/"),
  setRole: (userId: string, role: string) =>
    api.patch(`/users/${userId}/role?role=${role}`),
  deactivate: (userId: string) =>
    api.patch(`/users/${userId}/deactivate`),
};
