import axios from "axios";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
export const WS_BASE = API_BASE.replace(/^http/, "ws");

export const api = axios.create({ baseURL: API_BASE, withCredentials: false });

api.interceptors.request.use((cfg) => {
  if (typeof window !== "undefined") {
    const t = localStorage.getItem("token");
    if (t) cfg.headers.Authorization = `Bearer ${t}`;
  }
  return cfg;
});
