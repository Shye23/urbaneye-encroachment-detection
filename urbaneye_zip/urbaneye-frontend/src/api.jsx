const API_BASE_URL = "http://127.0.0.1:8000/api";

const getAccessToken = () => {
  return localStorage.getItem("access_token");
};

const getRefreshToken = () => {
  return localStorage.getItem("refresh_token");
};

const saveTokens = (data) => {
  if (data.access) {
    localStorage.setItem("access_token", data.access);
  }

  if (data.refresh) {
    localStorage.setItem("refresh_token", data.refresh);
  }
};

const clearAuth = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("username");
  localStorage.removeItem("role");
  localStorage.removeItem("anonymous_complaint");
};

const refreshAccessToken = async () => {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    return null;
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/auth/token/refresh/`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          refresh: refreshToken,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      clearAuth();
      return null;
    }

    saveTokens(data);

    return data.access;
  } catch (error) {
    console.error("Token refresh error:", error);
    clearAuth();
    return null;
  }
};

export const apiFetch = async (
  endpoint,
  options = {},
  retry = true
) => {
  let token = getAccessToken();

  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  // JSON request ke liye Content-Type
  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  let response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,
      headers,
    }
  );

  // Access token expired/invalid
  if (response.status === 401 && retry) {
    const newToken = await refreshAccessToken();

    if (newToken) {
      const retryHeaders = new Headers(options.headers || {});

      retryHeaders.set(
        "Authorization",
        `Bearer ${newToken}`
      );

      if (
        options.body &&
        !(options.body instanceof FormData) &&
        !retryHeaders.has("Content-Type")
      ) {
        retryHeaders.set(
          "Content-Type",
          "application/json"
        );
      }

      response = await fetch(
        `${API_BASE_URL}${endpoint}`,
        {
          ...options,
          headers: retryHeaders,
        }
      );
    }
  }

  return response;
};

export const apiJson = async (
  endpoint,
  options = {}
) => {

  const response = await apiFetch(
    endpoint,
    options
  );

  const text = await response.text();

  let data;

  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(
      `API returned invalid response (${response.status})`
    );
  }

  if (!response.ok) {
    throw new Error(
      data.detail ||
      data.error ||
      "Something went wrong."
    );
  }

  return data;
};
export const logout = () => {
  clearAuth();
  window.location.href = "/";
};