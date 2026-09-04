"use client";

/**
 * Map view — real road geometry and live traffic, per role.
 *
 * The legs each role cares about differ; the map component does not:
 *
 *   farmer  — farm → mandi (outbound only)
 *   trucker — depot → farm → mandi, then the return leg through a dealer
 *   dealer  — supplier/mandi → shop (the inbound delivery)
 *
 * Geometry comes from `POST /routes/live`, which asks TomTom for the actual
 * carriageway. When TomTom is unavailable the API returns a straight-line
 * estimate **labelled as such**, and this page shows that label rather than
 * passing an estimate off as a measured route.
 */

import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Card, ErrorState, Loading, Shell, Tag } from "@/components/app/Shell";
import { useSession } from "@/components/providers/SessionProvider";
import api, { apiFetch } from "@/lib/api";
import { t } from "@/lib/i18n";

const RouteMap = dynamic(() => import("@/components/map/RouteMap"), {
  ssr: false,
  loading: () => (
    <div className="grid h-[380px] place-items-center rounded-3xl border border-white/10 bg-neutral-950">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/20 border-t-lime-400" />
    </div>
  ),
});

// The demo corridor: Rohtak depot → Sonipat mandi, dealers along the way back.
const P = {
  depot:  { lat: 28.8955, lon: 76.6066, kind: "depot",  label: "रोहतक डिपो" },
  farm:   { lat: 28.99,   lon: 77.01,   kind: "farm",   label: "रामपुर कलां (खेत)" },
  mandi:  { lat: 28.9931, lon: 77.0151, kind: "mandi",  label: "सोनीपत मंडी" },
  dealer: { lat: 28.96,   lon: 76.85,   kind: "dealer", label: "सीमेंट डीलर" },
};

/** Which legs each role should see. */
function legsForRole(role) {
  if (role === "TRUCKER") {
    return {
      markers: [P.depot, P.farm, P.mandi, P.dealer],
      legs: [
        { from: P.depot, to: P.farm, kind: "outbound", label: "डिपो → खेत" },
        { from: P.farm, to: P.mandi, kind: "outbound", label: "खेत → मंडी" },
        { from: P.mandi, to: P.dealer, kind: "return", label: "मंडी → डीलर" },
        { from: P.dealer, to: P.depot, kind: "return", label: "डीलर → डिपो" },
      ],
      titleHi: "ट्रक चालक — पूरा चक्र",
    };
  }
  if (role === "INPUT_DEALER") {
    return {
      markers: [P.mandi, P.dealer],
      legs: [
        { from: P.mandi, to: P.dealer, kind: "outbound", label: "आपूर्ति → दुकान" },
      ],
      titleHi: "इनपुट डीलर — आने वाला सामान",
    };
  }
  return {
    markers: [P.farm, P.mandi],
    legs: [{ from: P.farm, to: P.mandi, kind: "outbound", label: "खेत → मंडी" }],
    titleHi: "किसान — खेत से मंडी",
  };
}

export default function MapPage() {
  const { lang, status, role } = useSession();
  const router = useRouter();
  const tr = (k) => t(k, lang);

  const [live, setLive] = useState(null);
  const [traffic, setTraffic] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const plan = legsForRole(role);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [routeRes, trafficRes] = await Promise.all([
        apiFetch("/routes/live", {
          method: "POST",
          body: JSON.stringify({
            legs: plan.legs.map((l) => ({
              from_point: { latitude: l.from.lat, longitude: l.from.lon },
              to_point: { latitude: l.to.lat, longitude: l.to.lon },
              kind: l.kind,
              label: l.label,
            })),
            travel_mode: "truck",
          }),
        }),
        apiFetch("/routes/live/traffic-config").catch(() => null),
      ]);
      setLive(routeRes);
      setTraffic(trafficRes?.available ? trafficRes : null);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, [role, JSON.stringify(plan.legs)]);

  useEffect(() => {
    if (status === "anon") router.replace("/signin");
    else if (status === "authed") load();
  }, [status, load, router]);

  if (status !== "authed") {
    return (
      <div className="min-h-screen bg-background">
        <Loading label={tr("common.loading")} />
      </div>
    );
  }

  // Flatten the returned geometry into outbound / return polylines.
  const outbound = [];
  const returnLine = [];
  (live?.legs || []).forEach((leg) => {
    (leg.kind === "return" ? returnLine : outbound).push(...(leg.polyline || []));
  });

  const home = role === "TRUCKER" ? "/app/trucker"
    : role === "INPUT_DEALER" ? "/app/dealer" : "/app/farmer";
  const nav = [
    { href: home, label: tr("nav.dashboard"), icon: "🏠" },
    { href: "/app/map", label: tr("route.title"), icon: "🗺️" },
  ];

  const isLive = live?.provider === "tomtom";
  const isMixed = live?.provider === "mixed";

  return (
    <Shell nav={nav} title={tr("route.title")}>
      {error && (
        <div className="mb-5">
          <ErrorState
            message={error.detail === "backend_unreachable"
              ? tr("common.backendDown") : error.message}
            onRetry={load}
            retryLabel={tr("common.retry")}
          />
        </div>
      )}

      <Card className="mb-5 p-0">
        <RouteMap
          markers={plan.markers}
          polyline={outbound}
          returnPolyline={returnLine}
          trafficConfig={traffic}
          height={400}
        />
      </Card>

      {/* Provenance, stated plainly. An estimate is never dressed up as live. */}
      <div className="mb-5 flex flex-wrap items-center gap-2 text-xs">
        <span className={`rounded-full border px-3 py-1 ${
          isLive ? "border-lime-400/40 bg-lime-400/10 text-lime-300"
                 : isMixed ? "border-amber-400/40 bg-amber-400/10 text-amber-300"
                 : "border-white/15 text-white/50"}`}>
          {isLive ? "असली सड़क मार्ग · TomTom"
            : isMixed ? "आंशिक रूप से असली मार्ग"
            : "अनुमानित सीधी दूरी"}
        </span>
        {traffic && (
          <span className="rounded-full border border-white/15 px-3 py-1 text-white/60">
            लाइव ट्रैफ़िक उपलब्ध
          </span>
        )}
        {live && (
          <span className="text-white/35">
            {live.legs.reduce((n, l) => n + l.n_geometry_points, 0)} geometry points
          </span>
        )}
      </div>

      {loading && <Loading label={tr("common.loading")} />}

      {/* Legs */}
      <Card className="mb-5">
        <Tag>{plan.titleHi}</Tag>
        <div className="mt-4 space-y-3">
          {(live?.legs || []).map((leg, i) => (
            <div key={i} className="flex items-start gap-3">
              <span
                className="mt-1.5 inline-block h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ background: leg.kind === "return" ? "#fbbf24" : "#a3e635" }}
              />
              <div className="min-w-0 flex-1">
                <p className="text-sm">{leg.label}</p>
                <p className="mt-0.5 text-xs text-white/45">
                  {leg.provider === "tomtom"
                    ? `${leg.n_geometry_points} बिंदु · असली सड़क`
                    : "अनुमानित सीधी रेखा"}
                  {leg.traffic_delay_min > 0 &&
                    ` · ट्रैफ़िक +${leg.traffic_delay_min} मिनट`}
                </p>
              </div>
              <span className="shrink-0 text-sm text-white/70">
                {leg.distance_km} {tr("common.km")}
              </span>
            </div>
          ))}
        </div>
      </Card>

      {live && (
        <Card>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Metric label={tr("route.distance")} value={live.total_distance_km}
                    unit={tr("common.km")} />
            <Metric label={tr("route.eta")} value={Math.round(live.total_time_min)}
                    unit={tr("common.min")} />
            <Metric label="ट्रैफ़िक देरी" value={live.total_traffic_delay_min}
                    unit={tr("common.min")} />
            <Metric label="वापसी लोड" value={returnLine.length > 1 ? "हाँ" : "—"}
                    accent={returnLine.length > 1} />
          </div>
          {live.warnings?.length > 0 && (
            <div className="mt-4 rounded-2xl border border-amber-500/25 bg-amber-500/5 p-3 text-xs text-amber-200">
              {live.warnings.map((w, i) => <p key={i}>{w}</p>)}
            </div>
          )}
          <p className="mt-4 text-[11px] text-white/30">{tr("route.engine")}</p>
        </Card>
      )}
    </Shell>
  );
}

function Metric({ label, value, unit, accent }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-white/40">{label}</p>
      <p className={`mt-1 text-xl font-medium ${accent ? "text-lime-400" : "text-white"}`}>
        {value}
        {unit && <span className="ml-1 text-sm text-white/50">{unit}</span>}
      </p>
    </div>
  );
}
