import axios from "axios";

const DEFAULT_API_BASE_URL = import.meta.env.DEV
  ? "http://localhost:8000"
  : "https://student-performance-backend-nujh.onrender.com";

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/+$/, "");

const api = axios.create({ baseURL: API_BASE_URL });

export function getApiErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).filter(Boolean).join("; ");
  }
  if (!error?.response) {
    return `Cannot reach the API at ${API_BASE_URL}. Check that the backend is running and VITE_API_BASE_URL is correct.`;
  }
  return error?.message || "The request could not be completed.";
}

export function reportApiError(error) {
  const message = getApiErrorMessage(error);
  window.dispatchEvent(new CustomEvent("edupredict:api-error", { detail: message }));
  return message;
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("edupredict_token") || sessionStorage.getItem("edupredict_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;
