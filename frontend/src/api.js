import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
});

let authContext = null;
let refreshPromise = null;

export function bindAuthContext(context) {
  authContext = context;
}

api.interceptors.request.use((config) => {
  if (authContext?.accessToken) {
    config.headers.Authorization = `Bearer ${authContext.accessToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const shouldRefresh =
      error.response?.status === 401 &&
      !originalRequest?._retry &&
      !originalRequest?.skipAuthRefresh &&
      authContext?.refreshToken;

    if (!shouldRefresh) {
      throw error;
    }

    originalRequest._retry = true;

    try {
      refreshPromise ||= authContext.refreshSession();
      await refreshPromise;
      refreshPromise = null;
      originalRequest.headers ||= {};
      originalRequest.headers.Authorization = `Bearer ${authContext.accessToken}`;
      return api(originalRequest);
    } catch (refreshError) {
      refreshPromise = null;
      authContext.logout();
      throw refreshError;
    }
  },
);

export default api;
