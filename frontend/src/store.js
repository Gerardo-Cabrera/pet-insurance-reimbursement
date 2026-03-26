import { computed, reactive } from "vue";

import api, { bindAuthContext } from "./api";

const ACCESS_TOKEN_KEY = "pir_access_token";
const REFRESH_TOKEN_KEY = "pir_refresh_token";

const state = reactive({
  user: null,
  accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
  refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
  loadingSession: false,
});

function persistTokens(access, refresh) {
  state.accessToken = access;
  state.refreshToken = refresh;

  if (access) {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
  } else {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
  }

  if (refresh) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}

export async function fetchProfile() {
  const { data } = await api.get("/auth/me/");
  state.user = data;
  return data;
}

export async function login(credentials) {
  const { data } = await api.post("/token/", credentials, {
    skipAuthRefresh: true,
  });
  persistTokens(data.access, data.refresh);
  await fetchProfile();
}

export async function register(payload) {
  await api.post("/auth/register/", payload, { skipAuthRefresh: true });
  await login({ email: payload.email, password: payload.password });
}

export async function refreshSession() {
  if (!state.refreshToken) {
    throw new Error("No refresh token available.");
  }

  const { data } = await api.post(
    "/token/refresh/",
    { refresh: state.refreshToken },
    { skipAuthRefresh: true },
  );
  persistTokens(data.access, state.refreshToken);
}

export async function hydrateSession() {
  if (!state.accessToken) {
    return;
  }

  state.loadingSession = true;
  try {
    await fetchProfile();
  } catch (error) {
    logout();
  } finally {
    state.loadingSession = false;
  }
}

export function logout() {
  state.user = null;
  persistTokens("", "");
}

export const isAuthenticated = computed(() => Boolean(state.accessToken && state.user));
export const isSupport = computed(() =>
  ["SUPPORT", "ADMIN"].includes(state.user?.role || ""),
);
export const canManagePets = computed(() =>
  ["CUSTOMER", "ADMIN"].includes(state.user?.role || ""),
);

bindAuthContext({
  get accessToken() {
    return state.accessToken;
  },
  get refreshToken() {
    return state.refreshToken;
  },
  refreshSession,
  logout,
});

export function useAuthStore() {
  return {
    state,
    isAuthenticated,
    isSupport,
    canManagePets,
    login,
    register,
    logout,
    hydrateSession,
  };
}
