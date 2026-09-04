"use client";

/**
 * RouteMap — the map UI layer.
 *
 * Deliberate separation, per the Phase-B architecture rule:
 *
 *     map UI (this file)
 *        ^ consumes plain {lat, lon} data
 *     routing data (RouteSolution / live legs from the API)
 *        ^ produced by
 *     routing algorithm (VB-QER)
 *        ^ independent of
 *     external map provider (OSM base tiles, TomTom traffic overlay)
 *
 * This component knows nothing about VB-QER, and VB-QER knows nothing about
 * Leaflet.
 *
 * **Degradation:** if base tiles fail (offline, blocked, rate-limited) the route
 * geometry and markers still render over the dark ground, and the UI says so.
 * The geometry is ours; the tiles are decoration.
 */

import { useEffect, useRef, useState } from "react";

const BASE_TILES = {
  url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
  attribution: "© OpenStreetMap contributors",
  maxZoom: 18,
};

const COLORS = {
  route: "#a3e635",      // lime-400, the brand accent
  returnLeg: "#fbbf24",  // amber — visually distinct from the outbound leg
};

/**
 * Role symbols instead of anonymous dots.
 *
 * A trucker glancing at a phone in a mandi yard should not have to decode a
 * colour legend to find their depot. Emoji are used rather than an icon
 * dependency: they render everywhere, need no sprite sheet, and survive a
 * tile-layer failure.
 */
const MARKER_STYLE = {
  farm:   { symbol: "🌾", ring: "#a3e635", labelHi: "खेत" },
  origin: { symbol: "🌾", ring: "#a3e635", labelHi: "खेत" },
  farmer: { symbol: "👨‍🌾", ring: "#a3e635", labelHi: "किसान" },
  mandi:  { symbol: "🏛️", ring: "#ef4444", labelHi: "मंडी" },
  dealer: { symbol: "🏪", ring: "#38bdf8", labelHi: "इनपुट डीलर" },
  depot:  { symbol: "🏠", ring: "#a78bfa", labelHi: "डिपो" },
  truck:  { symbol: "🚛", ring: "#f97316", labelHi: "ट्रक" },
  waypoint: { symbol: "•", ring: "#94a3b8", labelHi: "" },
};

/**
 * @param {Array<{lat:number, lon:number, kind:string, label?:string}>} markers
 * @param {Array<[number,number]>} polyline        outbound [[lat, lon], ...]
 * @param {Array<[number,number]>} returnPolyline  return leg
 * @param {{tile_url:string, attribution:string}|null} trafficConfig
 */
export default function RouteMap({
  markers = [],
  polyline = [],
  returnPolyline = [],
  trafficConfig = null,
  showTrafficDefault = true,
  height = 320,
  className = "",
}) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const trafficLayerRef = useRef(null);
  const [tilesFailed, setTilesFailed] = useState(false);
  const [ready, setReady] = useState(false);
  const [trafficOn, setTrafficOn] = useState(showTrafficDefault);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      // Leaflet touches `window` at import time, so it must load client-side only.
      const L = (await import("leaflet")).default;
      await import("leaflet/dist/leaflet.css");
      if (cancelled || !containerRef.current || mapRef.current) return;

      const map = L.map(containerRef.current, {
        zoomControl: true,
        attributionControl: true,
        scrollWheelZoom: false, // don't hijack page scroll on mobile
      });
      mapRef.current = map;

      const tiles = L.tileLayer(BASE_TILES.url, {
        attribution: BASE_TILES.attribution,
        maxZoom: BASE_TILES.maxZoom,
      });
      let failed = 0;
      tiles.on("tileerror", () => {
        failed += 1;
        if (failed > 3) setTilesFailed(true);
      });
      tiles.addTo(map);

      // Live traffic overlay, drawn above the base map but below the route so
      // the chosen path is never obscured by congestion colouring.
      if (trafficConfig?.tile_url) {
        const traffic = L.tileLayer(trafficConfig.tile_url, {
          attribution: trafficConfig.attribution || "© TomTom",
          maxZoom: 18,
          opacity: 0.85,
        });
        trafficLayerRef.current = traffic;
        if (trafficOn) traffic.addTo(map);
      }

      const bounds = [];

      if (polyline.length > 1) {
        // Casing underneath keeps the route readable over busy traffic tiles.
        L.polyline(polyline, {
          color: "#0a0a0a", weight: 9, opacity: 0.55,
        }).addTo(map);
        L.polyline(polyline, {
          color: COLORS.route, weight: 5, opacity: 0.95, lineJoin: "round",
        }).addTo(map);
        bounds.push(...polyline);
      }

      if (returnPolyline.length > 1) {
        L.polyline(returnPolyline, {
          color: "#0a0a0a", weight: 9, opacity: 0.5,
        }).addTo(map);
        L.polyline(returnPolyline, {
          color: COLORS.returnLeg, weight: 5, opacity: 0.95,
          dashArray: "10 8", lineJoin: "round",
        }).addTo(map);
        bounds.push(...returnPolyline);
      }

      markers.forEach((m) => {
        if (m.lat == null || m.lon == null) return;
        const style = MARKER_STYLE[m.kind] || MARKER_STYLE.waypoint;
        const icon = L.divIcon({
          className: "vb-marker",
          html: `<div style="
              display:grid;place-items:center;
              width:36px;height:36px;border-radius:50%;
              background:#0a0a0af2;border:2.5px solid ${style.ring};
              box-shadow:0 2px 10px #000a, 0 0 0 3px ${style.ring}33;
              font-size:18px;line-height:1;">${style.symbol}</div>`,
          iconSize: [36, 36],
          iconAnchor: [18, 18],
        });
        const label = m.label || style.labelHi || "";
        const marker = L.marker([m.lat, m.lon], { icon, zIndexOffset: 500 }).addTo(map);
        if (label) {
          marker.bindTooltip(label, {
            permanent: false, direction: "top", offset: [0, -14],
          });
        }
        bounds.push([m.lat, m.lon]);
      });

      if (bounds.length > 1) {
        map.fitBounds(bounds, { padding: [45, 45], maxZoom: 13 });
      } else if (bounds.length === 1) {
        map.setView(bounds[0], 12);
      } else {
        // Nothing to show: centre on the project region rather than [0,0].
        map.setView([28.95, 76.9], 9);
      }

      setReady(true);
    })();

    return () => {
      cancelled = true;
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        trafficLayerRef.current = null;
      }
    };
  }, [
    JSON.stringify(markers),
    JSON.stringify(polyline),
    JSON.stringify(returnPolyline),
    trafficConfig?.tile_url,
  ]);

  // Toggle traffic without rebuilding the whole map.
  useEffect(() => {
    const map = mapRef.current;
    const layer = trafficLayerRef.current;
    if (!map || !layer) return;
    if (trafficOn) layer.addTo(map);
    else map.removeLayer(layer);
  }, [trafficOn]);

  const kindsShown = [...new Set(markers.map((m) => m.kind))];

  return (
    <div className={`relative overflow-hidden rounded-3xl border border-white/10 ${className}`}>
      <div
        ref={containerRef}
        style={{ height, background: "#0a0a0a" }}
        className="w-full"
        data-testid="route-map"
      />

      {!ready && (
        <div className="absolute inset-0 grid place-items-center bg-neutral-950/80">
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/20 border-t-lime-400" />
        </div>
      )}

      {tilesFailed && (
        <div className="absolute left-3 top-16 z-[1200] rounded-full border border-amber-500/30 bg-neutral-950/90 px-3 py-1 text-[11px] text-amber-300">
          नक्शा टाइल उपलब्ध नहीं — रास्ता फिर भी दिखाया गया है
        </div>
      )}

      {/* Traffic toggle. Only offered when a key can actually serve tiles. */}
      {trafficConfig?.tile_url && (
        <button
          onClick={() => setTrafficOn((v) => !v)}
          className={`absolute bottom-3 left-3 z-[1200] flex items-center gap-2 rounded-full border px-3 py-1.5 text-[11px] transition ${
            trafficOn
              ? "border-lime-400/50 bg-lime-400/15 text-lime-300"
              : "border-white/15 bg-neutral-950/90 text-white/60"
          }`}
        >
          <span className={`inline-block h-2 w-2 rounded-full ${
            trafficOn ? "bg-lime-400" : "bg-white/30"}`} />
          ट्रैफ़िक
        </button>
      )}

      {/* Legend. Above Leaflet's own panes (z 400–1000), which would otherwise
          render on top of it. */}
      <div className="pointer-events-none absolute right-3 top-3 z-[1200] max-w-[62%] rounded-2xl border border-white/10 bg-neutral-950/92 px-3 py-2 text-[11px] text-white/80">
        <div className="flex flex-wrap gap-x-3 gap-y-1">
          <LineKey color={COLORS.route} label="जाने का रास्ता" />
          {returnPolyline.length > 1 && (
            <LineKey color={COLORS.returnLeg} dashed label="वापसी लोड" />
          )}
        </div>
        {kindsShown.length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 border-t border-white/10 pt-1.5">
            {kindsShown.map((k) => {
              const st = MARKER_STYLE[k] || MARKER_STYLE.waypoint;
              return (
                <span key={k} className="flex items-center gap-1">
                  <span>{st.symbol}</span>
                  <span className="text-white/60">{st.labelHi}</span>
                </span>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function LineKey({ color, label, dashed }) {
  return (
    <span className="flex items-center gap-1.5">
      <span
        className="inline-block h-[3px] w-5 rounded-full"
        style={{
          background: dashed
            ? `repeating-linear-gradient(90deg, ${color} 0 5px, transparent 5px 9px)`
            : color,
        }}
      />
      {label}
    </span>
  );
}
