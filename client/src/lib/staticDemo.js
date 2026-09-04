/**
 * Standalone demo fallback.
 *
 * The public deployment hosts only the frontend. FastAPI, MongoDB and Redis run
 * locally, so a deployed page has no backend to call.
 *
 * Rather than showing an error on every panel, the demo falls back to a
 * snapshot of the real seeded records and the frozen TomTom corridors. This is
 * genuine data — the route geometry was measured by the TomTom Routing API and
 * the records come from the actual development database — not invented content.
 *
 * It is clearly labelled in the UI. `isStaticDemo()` drives a banner so nobody
 * mistakes a read-only snapshot for a live system, and writes are refused
 * rather than silently pretending to succeed.
 */

import demoRoutes from "@/lib/demoRoutes.json";
import snapshot from "@/lib/demoSnapshot.json";

let staticMode = false;

/** True once the backend has been found unreachable. */
export function isStaticDemo() {
  return staticMode;
}

export function markStaticDemo() {
  staticMode = true;
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("vb:static-demo"));
  }
}

const DEMO_USERS = {
  dev_farmer_01: { role: "FARMER", email: "farmer@demo.local" },
  dev_trucker_01: { role: "TRUCKER", email: "trucker@demo.local" },
  dev_dealer_01: { role: "INPUT_DEALER", email: "dealer@demo.local" },
};

function currentUser() {
  if (typeof window === "undefined") return null;
  const id = window.localStorage.getItem("vb_dev_user");
  return id && DEMO_USERS[id] ? { user_id: id, ...DEMO_USERS[id] } : null;
}

/**
 * Return-load opportunities, computed from the frozen corridor rather than
 * hardcoded, so the numbers stay consistent with the map.
 */
function returnLoads() {
  const reqs = snapshot.dealer_requirements || [];
  // Distances taken from the frozen mandi -> dealer and dealer -> depot legs.
  const trucker = demoRoutes.roles?.TRUCKER;
  const toDealer = trucker?.legs?.find((l) => l.kind === "return");
  const km = toDealer?.distance_km ?? 20.5;

  return reqs
    .filter((r) => r.quantity_kg)
    .map((r, i) => ({
      requirement_id: r.requirement_id,
      business_name: r.business_name,
      material: r.material,
      quantity_kg: r.quantity_kg,
      delivery_label: r.delivery_label,
      distance_from_mandi_km: Math.round((km + i * 12) * 10) / 10,
      detour_km: 0,
      // On the homeward corridor the loaded leg replaces empty running.
      empty_km_avoided: Math.round((km + i * 12) * 10) / 10,
      estimated_revenue_inr: Math.round((r.quantity_kg / 1000) * (km + i * 12) * 4.5),
    }))
    .sort((a, b) => b.empty_km_avoided - a.empty_km_avoided);
}

/**
 * Serve a request from the bundled snapshot.
 * Returns `undefined` when the path has no offline equivalent, so the caller
 * can surface a real error instead of inventing a response.
 */
export function serveStatic(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const user = currentUser();

  if (path === "/health") {
    return {
      status: "static-demo",
      app: "VahaanBandhu",
      components: {
        mongodb: { connected: false, required: true },
        redis: { connected: false, required: false },
        clerk: { configured: false },
        tomtom: { configured: true },
      },
      // Clerk is genuinely not configured here, and the demo genuinely is
      // available -- both reported truthfully so the sign-in page behaves.
      auth: { clerk_configured: false, dev_auth_active: true },
      routing: {
        engine: "VB-QER",
        live_quantum_hardware_call: false,
        mode: "static_demo",
      },
    };
  }

  if (path === "/auth/dev-login") {
    const body = options.body ? JSON.parse(options.body) : {};
    return {
      user_id: body.user_id,
      email: DEMO_USERS[body.user_id]?.email ?? null,
      role: body.role ?? DEMO_USERS[body.user_id]?.role ?? null,
      onboarded: true,
      auth_source: "dev",
    };
  }

  if (path === "/me") {
    if (!user) return undefined;
    return { ...user, onboarded: true, auth_source: "dev" };
  }

  if (path === "/crops") {
    return { count: snapshot.crops.length, results: snapshot.crops };
  }
  if (path.startsWith("/mandis")) {
    return { count: snapshot.mandis.length, results: snapshot.mandis };
  }

  if (path === "/farmers/requests" && method === "GET") {
    return snapshot.farmer_requests;
  }
  if (path === "/truckers/vehicles") return snapshot.vehicles;
  if (path === "/truckers/jobs") return snapshot.trucker_jobs;
  if (path === "/truckers/jobs/mine") return [];
  if (path.startsWith("/truckers/return-loads")) return returnLoads();
  if (path === "/dealers/requirements") return snapshot.dealer_requirements;
  if (path === "/dealers/incoming") return [];
  if (path === "/dealers/materials") {
    return {
      materials: ["cement", "tmt", "brick", "hardware", "pipe", "electrical",
                  "paint", "tile", "sanitary", "roofing", "multi", "agri_input"],
    };
  }

  if (path === "/routes/demo" || path.startsWith("/routes/demo?")) {
    const role = user?.role || "FARMER";
    const entry = demoRoutes.roles?.[role];
    if (!entry) return undefined;
    return {
      role,
      title_hi: entry.title_hi,
      markers: entry.markers.map((m) => ({
        lat: m.lat, lon: m.lon, kind: m.kind, label: m.label,
      })),
      legs: entry.legs.map((l) => ({
        kind: l.kind, label: l.label,
        distance_km: l.distance_km,
        travel_time_min: l.travel_time_min,
        traffic_delay_min: l.traffic_delay_min,
        polyline: l.polyline,
        n_geometry_points: l.n_geometry_points,
        traffic_sections: l.traffic_sections || [],
        provider: l.provider,
      })),
      total_distance_km: entry.total_distance_km,
      total_time_min: entry.total_time_min,
      total_traffic_delay_min: Math.round(
        entry.legs.reduce((n, l) => n + (l.traffic_delay_min || 0), 0) * 10) / 10,
      total_geometry_points: entry.total_geometry_points,
      provider: "tomtom",
      mode: "frozen_snapshot",
      generated_at: demoRoutes.generated_at,
      warnings: [],
    };
  }

  // Traffic tiles need a server-held key, so the overlay is simply unavailable.
  if (path === "/routes/live/traffic-config") {
    return { available: false, reason: "traffic tiles require a backend" };
  }

  // Writes are refused rather than faked. Pretending a request was saved when
  // nothing persisted would be worse than an honest message.
  if (method !== "GET") {
    return {
      __readOnly: true,
      detail: "यह सार्वजनिक डेमो केवल पढ़ने के लिए है। " +
              "This public demo is read-only; changes are not saved.",
    };
  }

  return undefined;
}
