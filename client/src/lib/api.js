/**
 * VahaanBandhu API client.
 *
 * All backend access goes through here so auth headers, error shapes and the
 * base URL live in exactly one place.
 *
 * Auth: in production the Clerk session token is attached as a bearer. In local
 * development, when Clerk is not configured, an `x-dev-user` header identifies
 * the seeded demo user. The backend decides which it accepts -- the frontend
 * never asserts a role, because the server reads the role from the database.
 */

const BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const PREFIX = "/api/v1";

/** Thrown for any non-2xx response, carrying the backend's detail message. */
export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function devUser() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("vb_dev_user");
}

export async function apiFetch(path, options = {}) {
  const { token, devUserId, ...rest } = options;
  const headers = {
    "Content-Type": "application/json",
    ...(rest.headers || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  } else {
    const dev = devUserId || devUser();
    if (dev) headers["x-dev-user"] = dev;
  }

  let res;
  try {
    res = await fetch(`${BASE}${PREFIX}${path}`, { ...rest, headers });
  } catch (e) {
    // Network-level failure: the API is unreachable. Surface this distinctly so
    // the UI can say "backend unavailable" rather than a blank screen.
    throw new ApiError(
      "सर्वर से संपर्क नहीं हो पा रहा है।",
      0,
      "backend_unreachable"
    );
  }

  if (res.status === 204) return null;

  let body = null;
  try {
    body = await res.json();
  } catch {
    body = null;
  }

  if (!res.ok) {
    throw new ApiError(
      body?.detail || `Request failed (${res.status})`,
      res.status,
      body?.detail
    );
  }
  return body;
}

/* ------------------------------------------------------------------ */
/* Identity                                                            */
/* ------------------------------------------------------------------ */

export const api = {
  health: () => apiFetch("/health"),
  engineInfo: () => apiFetch("/routes/engine/info"),

  me: (opts) => apiFetch("/me", opts),
  selectRole: (payload, opts) =>
    apiFetch("/me/role", { method: "POST", body: JSON.stringify(payload), ...opts }),
  devLogin: (payload) =>
    apiFetch("/auth/dev-login", { method: "POST", body: JSON.stringify(payload) }),

  /* Reference data */
  crops: () => apiFetch("/crops"),
  mandis: (limit = 60) => apiFetch(`/mandis?limit=${limit}`),
  searchLocations: (q, type) =>
    apiFetch(
      `/locations/search?q=${encodeURIComponent(q)}${type ? `&location_type=${type}` : ""}`
    ),

  /* Farmer */
  farmer: {
    profile: (opts) => apiFetch("/farmers/profile", opts),
    listRequests: (opts) => apiFetch("/farmers/requests", opts),
    getRequest: (id, opts) => apiFetch(`/farmers/requests/${id}`, opts),
    createRequest: (payload, opts) =>
      apiFetch("/farmers/requests", {
        method: "POST",
        body: JSON.stringify(payload),
        ...opts,
      }),
    resolveQuantity: (id, bagWeightKg, opts) =>
      apiFetch(`/farmers/requests/${id}/resolve-quantity`, {
        method: "POST",
        body: JSON.stringify({ bag_weight_kg: bagWeightKg }),
        ...opts,
      }),
  },

  /* Trucker */
  trucker: {
    profile: (opts) => apiFetch("/truckers/profile", opts),
    vehicles: (opts) => apiFetch("/truckers/vehicles", opts),
    addVehicle: (payload, opts) =>
      apiFetch("/truckers/vehicles", {
        method: "POST",
        body: JSON.stringify(payload),
        ...opts,
      }),
    setAvailability: (vehicleId, payload, opts) =>
      apiFetch(`/truckers/vehicles/${vehicleId}/availability`, {
        method: "POST",
        body: JSON.stringify(payload),
        ...opts,
      }),
    jobs: (opts) => apiFetch("/truckers/jobs", opts),
    myJobs: (opts) => apiFetch("/truckers/jobs/mine", opts),
    acceptJob: (requestId, vehicleId, opts) =>
      apiFetch(`/truckers/jobs/${requestId}/accept`, {
        method: "POST",
        body: JSON.stringify({ vehicle_id: vehicleId }),
        ...opts,
      }),
    updateStatus: (requestId, status, opts) =>
      apiFetch(`/truckers/jobs/${requestId}/status`, {
        method: "POST",
        body: JSON.stringify({ status }),
        ...opts,
      }),
    returnLoads: (params, opts) => {
      const q = new URLSearchParams(params).toString();
      return apiFetch(`/truckers/return-loads?${q}`, opts);
    },
  },

  /* Input dealer */
  dealer: {
    profile: (opts) => apiFetch("/dealers/profile", opts),
    materials: () => apiFetch("/dealers/materials"),
    listRequirements: (opts) => apiFetch("/dealers/requirements", opts),
    createRequirement: (payload, opts) =>
      apiFetch("/dealers/requirements", {
        method: "POST",
        body: JSON.stringify(payload),
        ...opts,
      }),
    incoming: (opts) => apiFetch("/dealers/incoming", opts),
  },

  /* Routing — always VB-QER, never an individual solver */
  routes: {
    optimize: (payload, opts) =>
      apiFetch("/routes/optimize", {
        method: "POST",
        body: JSON.stringify(payload),
        ...opts,
      }),
    optimizeForRequest: (requestId, opts) =>
      apiFetch(`/routes/optimize/request/${requestId}`, {
        method: "POST",
        ...opts,
      }),
    get: (routeId, opts) => apiFetch(`/routes/${routeId}`, opts),
  },
};

export default api;
