"use client";

/**
 * Route result.
 *
 * Shows what VB-QER decided and, importantly, *why* — in plain Hindi. The farmer
 * gets reasons, not a research report: no QUBO, no bitstrings, no QAOA
 * parameters. Version provenance is available but tucked into a collapsed
 * technical section for debugging.
 */

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Card, ErrorState, Loading, Shell, Tag } from "@/components/app/Shell";
import { useSession } from "@/components/providers/SessionProvider";
import api from "@/lib/api";
import { t } from "@/lib/i18n";

export default function RoutePage() {
  const { lang, status } = useSession();
  const { requestId } = useParams();
  const router = useRouter();
  const tr = (k) => t(k, lang);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showTech, setShowTech] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await api.routes.optimizeForRequest(requestId));
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, [requestId]);

  useEffect(() => {
    if (status === "anon") router.replace("/signin");
    else if (status === "authed") load();
  }, [status, load, router]);

  const nav = [{ href: "/app/farmer", label: tr("nav.dashboard"), icon: "🏠" }];
  const sol = data?.solution;
  const reasons = lang === "hi"
    ? sol?.explanation?.reasons_hi
    : sol?.explanation?.reasons_en;

  return (
    <Shell nav={nav} title={tr("route.title")}>
      <Link
        href="/app/farmer"
        className="mb-5 inline-block text-sm text-white/50 hover:text-white"
      >
        ← {tr("nav.dashboard")}
      </Link>

      {loading && <Loading label={tr("common.loading")} />}

      {error && (
        <ErrorState
          message={error.detail === "backend_unreachable"
            ? tr("common.backendDown") : error.message}
          onRetry={load}
          retryLabel={tr("common.retry")}
        />
      )}

      {sol && (
        <>
          {/* Headline numbers */}
          <Card className="mb-5">
            <div className="grid grid-cols-2 gap-5 sm:grid-cols-4">
              <Metric
                label={tr("route.distance")}
                value={`${sol.distance_km}`}
                unit={tr("common.km")}
              />
              <Metric
                label={tr("route.eta")}
                value={`${Math.round(sol.estimated_time_min)}`}
                unit={tr("common.min")}
              />
              <Metric
                label={tr("route.cost")}
                value={`₹${Math.round(sol.total_estimated_cost_inr)}`}
              />
              <Metric
                label={tr("route.emptyKm")}
                value={`${sol.empty_km}`}
                unit={tr("common.km")}
                accent={sol.empty_km === 0}
              />
            </div>
          </Card>

          {/* Why this route — plain language */}
          {reasons?.length > 0 && (
            <Card className="mb-5">
              <Tag>{tr("route.why")}</Tag>
              <ul className="mt-4 space-y-2">
                {reasons.map((r, i) => (
                  <li key={i} className="flex gap-3 text-sm text-white/75">
                    <span className="text-lime-400">•</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
              {sol.explanation?.margin_is_decisive === false && (
                <p className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-3 text-xs text-white/50">
                  {lang === "hi"
                    ? "इस रास्ते और अगले विकल्प में बहुत कम अंतर है।"
                    : "This route and the next option are very close."}
                </p>
              )}
            </Card>
          )}

          {/* Return-load opportunity, when VB-QER found one */}
          {sol.return_load?.available && (
            <Card className="mb-5 border-lime-400/25 bg-lime-400/[0.06]">
              <Tag>{t("trucker.returnLoads", lang)}</Tag>
              <p className="mt-3 text-2xl font-medium text-lime-400">
                {sol.empty_km_avoided} {tr("common.km")}
              </p>
              <p className="text-xs uppercase tracking-wide text-white/40">
                {t("trucker.emptyKmAvoided", lang)}
              </p>
            </Card>
          )}

          {data.warnings?.length > 0 && (
            <div className="mb-5 rounded-2xl border border-amber-500/25 bg-amber-500/5 p-4 text-sm text-amber-200">
              {data.warnings.map((w, i) => (
                <p key={i}>{w}</p>
              ))}
            </div>
          )}

          {/* Provenance, collapsed. Useful for debugging, not for the farmer. */}
          <button
            onClick={() => setShowTech((s) => !s)}
            className="text-xs text-white/35 hover:text-white/60"
          >
            {showTech ? "▾" : "▸"} {tr("route.engine")}
          </button>
          {showTech && (
            <Card className="mt-3 text-xs text-white/50">
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2">
                <Row k="engine" v="VB-QER" />
                <Row k="version" v={sol.optimization?.vbqer_version} />
                <Row k="problem_type" v={sol.optimization?.problem_type} />
                <Row k="route_source" v={sol.optimization?.final_route_source} />
                <Row k="cost_snapshot" v={sol.optimization?.cost_snapshot_id} />
                <Row
                  k="quantum_artifact_used"
                  v={String(sol.optimization?.quantum_artifact_used)}
                />
                <Row
                  k="live_qpu_call"
                  v={String(sol.optimization?.quantum_hardware_called_live)}
                />
                <Row k="cached" v={String(sol.optimization?.cached)} />
              </dl>
            </Card>
          )}
        </>
      )}
    </Shell>
  );
}

function Metric({ label, value, unit, accent }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-white/40">{label}</p>
      <p
        className={`mt-1 text-2xl font-medium ${
          accent ? "text-lime-400" : "text-white"
        }`}
      >
        {value}
        {unit && <span className="ml-1 text-sm text-white/50">{unit}</span>}
      </p>
    </div>
  );
}

function Row({ k, v }) {
  return (
    <>
      <dt className="text-white/35">{k}</dt>
      <dd className="truncate font-mono text-white/70">{v ?? "—"}</dd>
    </>
  );
}
