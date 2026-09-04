"use client";

/**
 * Trucker experience.
 *
 * The differentiator is the return-load panel. A trucker's real economics are
 * dominated by empty running, so `empty_km_avoided` is given the most visual
 * weight on the page — it is the number that decides whether a job is worth
 * taking, and it is computed, never illustrative.
 */

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  Card, EmptyState, ErrorState, Loading, Shell, StatusPill, Tag,
} from "@/components/app/Shell";
import { useSession } from "@/components/providers/SessionProvider";
import api from "@/lib/api";
import { t } from "@/lib/i18n";

// The dev trucker is based near Rohtak; the mandi corridor runs east to Sonipat.
const HOME = { lat: 28.8955, lon: 76.6066 };
const MANDI = { lat: 28.9931, lon: 77.0151 };

export default function TruckerPage() {
  const { lang, status } = useSession();
  const router = useRouter();
  const tr = (k) => t(k, lang);

  const [vehicles, setVehicles] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [myJobs, setMyJobs] = useState([]);
  const [returns, setReturns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("jobs");

  const nav = [
    { href: "/app/trucker", label: tr("nav.dashboard"), icon: "🏠" },
    { href: "/app/map", label: tr("route.title"), icon: "🗺️" },
  ];

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [v, j, mj] = await Promise.all([
        api.trucker.vehicles(),
        api.trucker.jobs(),
        api.trucker.myJobs(),
      ]);
      setVehicles(v || []);
      setJobs(j || []);
      setMyJobs(mj || []);

      const cap = v?.[0]?.capacity_kg || 9000;
      const rl = await api.trucker.returnLoads({
        latitude: MANDI.lat, longitude: MANDI.lon,
        home_latitude: HOME.lat, home_longitude: HOME.lon,
        capacity_kg: cap, max_km: 90,
      });
      setReturns(rl || []);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (status === "anon") router.replace("/signin");
    else if (status === "authed") load();
  }, [status, load, router]);

  async function toggleAvailability(v) {
    try {
      await api.trucker.setAvailability(v.vehicle_id, {
        available: !v.available,
        point: { latitude: HOME.lat, longitude: HOME.lon },
      });
      await load();
    } catch (e) {
      setError(e);
    }
  }

  async function accept(job) {
    try {
      await api.trucker.acceptJob(job.request_id, vehicles[0]?.vehicle_id);
      await load();
    } catch (e) {
      setError(e);
    }
  }

  if (status !== "authed") {
    return (
      <div className="min-h-screen bg-background">
        <Loading label={tr("common.loading")} />
      </div>
    );
  }

  return (
    <Shell nav={nav} title={tr("trucker.title")}>
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

      {/* Vehicle + availability */}
      {vehicles.map((v) => (
        <Card key={v.vehicle_id} className="mb-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-white/40">
                {tr("trucker.myVehicle")}
              </p>
              <p className="mt-1 text-xl font-medium">{v.vehicle_number}</p>
              <p className="mt-0.5 text-sm text-white/50">
                {v.vehicle_class} · {tr("trucker.capacity")}{" "}
                {v.capacity_kg?.toLocaleString()} {t("unit.kg", lang)}
              </p>
            </div>
            <button
              onClick={() => toggleAvailability(v)}
              className={`h-12 rounded-full border px-6 text-sm font-medium transition ${
                v.available
                  ? "border-lime-400 bg-lime-400 text-neutral-950"
                  : "border-white/20 text-white/70"
              }`}
            >
              {v.available ? tr("trucker.available") : tr("trucker.unavailable")}
            </button>
          </div>
        </Card>
      ))}

      {/* CIRCULAR LOGISTICS — the product thesis, given top billing */}
      <Card className="mb-6 border-lime-400/25 bg-gradient-to-br from-lime-400/[0.07] to-transparent">
        <Tag>{tr("trucker.returnLoads")}</Tag>
        <p className="mt-3 text-sm text-white/60">
          {tr("trucker.returnLoads.desc")}
        </p>

        {returns.length === 0 ? (
          <p className="mt-5 text-sm text-white/40">{tr("trucker.noReturnLoads")}</p>
        ) : (
          <div className="mt-4 space-y-3">
            {returns.map((r) => (
              <div
                key={r.requirement_id}
                className="rounded-2xl border border-white/10 bg-neutral-950/60 p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-medium">{r.material}</p>
                    <p className="mt-0.5 text-sm text-white/50">
                      {r.business_name}
                    </p>
                    <p className="mt-0.5 text-sm text-white/40">
                      {r.quantity_kg?.toLocaleString()} {t("unit.kg", lang)}
                    </p>
                  </div>
                  {/* The number that decides the job */}
                  <div className="text-right">
                    <p className="text-2xl font-medium text-lime-400">
                      {r.empty_km_avoided} {tr("common.km")}
                    </p>
                    <p className="text-[11px] uppercase tracking-wide text-white/40">
                      {tr("trucker.emptyKmAvoided")}
                    </p>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-white/50">
                  <span>
                    {tr("trucker.detour")}: {r.detour_km} {tr("common.km")}
                  </span>
                  <span>
                    {tr("trucker.earning")}: ₹{r.estimated_revenue_inr}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Jobs */}
      <div className="mb-4 flex gap-2">
        {[
          ["jobs", tr("trucker.openJobs"), jobs.length],
          ["mine", tr("trucker.myJobs"), myJobs.length],
        ].map(([key, label, n]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`h-11 rounded-full border px-5 text-sm transition ${
              tab === key
                ? "border-lime-400 bg-lime-400 font-medium text-neutral-950"
                : "border-white/15 text-white/70"
            }`}
          >
            {label} ({n})
          </button>
        ))}
      </div>

      {loading && <Loading label={tr("common.loading")} />}

      {!loading && (tab === "jobs" ? jobs : myJobs).length === 0 && (
        <EmptyState icon="🚛" title={tr("trucker.noJobs")} />
      )}

      <div className="space-y-3">
        {(tab === "jobs" ? jobs : myJobs).map((j) => (
          <Card key={j.request_id}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-lg font-medium">{j.crop_label || j.crop_key}</p>
                <p className="mt-1 text-sm text-white/60">
                  {j.quantity_kg?.toLocaleString()} {t("unit.kg", lang)}
                </p>
                {j.mandi_label && (
                  <p className="mt-0.5 text-sm text-white/40">→ {j.mandi_label}</p>
                )}
                {j.origin_label && (
                  <p className="mt-0.5 text-sm text-white/40">
                    {j.origin_label} से
                  </p>
                )}
              </div>
              <StatusPill status={j.status} lang={lang} />
            </div>

            {tab === "jobs" && vehicles.length > 0 && (
              <button
                onClick={() => accept(j)}
                className="mt-4 h-11 w-full rounded-full border border-lime-400 bg-lime-400 text-sm font-medium text-neutral-950 sm:w-auto sm:px-6"
              >
                {tr("trucker.accept")}
              </button>
            )}
          </Card>
        ))}
      </div>
    </Shell>
  );
}
