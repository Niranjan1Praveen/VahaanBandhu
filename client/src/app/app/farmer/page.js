"use client";

/**
 * Farmer experience.
 *
 * Designed for minimal typing on a phone: crop and mandi are pickers, quantity
 * is a number plus a unit chip row, and the whole form fits above the fold on a
 * 390px screen.
 *
 * The bori rule is visible in the UI: when the backend cannot resolve a
 * quantity to kilograms it returns a clarification prompt, and the request sits
 * in DRAFT until the farmer supplies a bag weight. It is never silently converted.
 */

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  Card, EmptyState, ErrorState, Loading, Shell, StatusPill, Tag,
} from "@/components/app/Shell";
import { useSession } from "@/components/providers/SessionProvider";
import api from "@/lib/api";
import { t } from "@/lib/i18n";

const UNITS = ["quintal", "bori", "kg", "tonne"];

export default function FarmerPage() {
  const { lang, user, status } = useSession();
  const router = useRouter();
  const tr = (k) => t(k, lang);

  const [crops, setCrops] = useState([]);
  const [mandis, setMandis] = useState([]);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    crop_key: "", mandi_id: "", quantity_value: "",
    quantity_unit: "quintal", origin_label: "",
  });

  const nav = [
    { href: "/app/farmer", label: tr("nav.dashboard"), icon: "🏠" },
    { href: "/app/map", label: tr("route.title"), icon: "🗺️" },
  ];

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [c, m, r] = await Promise.all([
        api.crops(), api.mandis(60), api.farmer.listRequests(),
      ]);
      setCrops(c.results || []);
      setMandis(m.results || []);
      setRequests(r || []);
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

  async function submit(e) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const crop = crops.find((c) => c.crop_key === form.crop_key);
      const mandi = mandis.find((m) => m.mandi_id === form.mandi_id);
      await api.farmer.createRequest({
        crop_key: form.crop_key,
        crop_label: crop?.name_hi || crop?.name_en,
        mandi_id: form.mandi_id || null,
        mandi_label: mandi?.name_hi || mandi?.apmc_name,
        quantity_value: Number(form.quantity_value),
        quantity_unit: form.quantity_unit,
        origin_label: form.origin_label,
        language: lang,
      });
      setShowForm(false);
      setForm({
        crop_key: "", mandi_id: "", quantity_value: "",
        quantity_unit: "quintal", origin_label: "",
      });
      await load();
    } catch (e2) {
      setError(e2);
    } finally {
      setSubmitting(false);
    }
  }

  async function resolveBori(requestId, kg) {
    try {
      await api.farmer.resolveQuantity(requestId, Number(kg));
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
    <Shell nav={nav} title={tr("farmer.title")}>
      {/* Create request */}
      <div className="mb-6">
        {!showForm ? (
          <button
            onClick={() => setShowForm(true)}
            className="h-14 w-full rounded-full border border-lime-400 bg-lime-400 text-base font-medium text-neutral-950 transition active:scale-[0.99]"
          >
            + {tr("farmer.newRequest")}
          </button>
        ) : (
          <Card>
            <div className="mb-4 flex items-center justify-between">
              <Tag>{tr("farmer.newRequest")}</Tag>
              <button
                onClick={() => setShowForm(false)}
                className="text-sm text-white/50 hover:text-white"
              >
                {tr("common.cancel")}
              </button>
            </div>

            <form onSubmit={submit} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm text-white/70">
                  {tr("farmer.crop")}
                </label>
                <select
                  required
                  value={form.crop_key}
                  onChange={(e) => setForm((f) => ({ ...f, crop_key: e.target.value }))}
                  className="h-12 w-full rounded-2xl border border-white/15 bg-neutral-900 px-4 text-base outline-none focus:border-lime-400"
                >
                  <option value="">—</option>
                  {crops.map((c) => (
                    <option key={c.crop_key} value={c.crop_key}>
                      {c.name_hi} ({c.name_en})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1.5 block text-sm text-white/70">
                  {tr("farmer.mandi")}
                </label>
                <select
                  value={form.mandi_id}
                  onChange={(e) => setForm((f) => ({ ...f, mandi_id: e.target.value }))}
                  className="h-12 w-full rounded-2xl border border-white/15 bg-neutral-900 px-4 text-base outline-none focus:border-lime-400"
                >
                  <option value="">—</option>
                  {mandis.map((m) => (
                    <option key={m.mandi_id} value={m.mandi_id}>
                      {m.name_hi || m.apmc_name} · {m.district}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1.5 block text-sm text-white/70">
                  {tr("farmer.quantity")}
                </label>
                <input
                  required
                  type="number"
                  step="0.1"
                  min="0.1"
                  inputMode="decimal"
                  value={form.quantity_value}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, quantity_value: e.target.value }))
                  }
                  className="h-12 w-full rounded-2xl border border-white/15 bg-neutral-900 px-4 text-base outline-none focus:border-lime-400"
                />
                {/* Unit chips: fewer taps than a select on mobile */}
                <div className="mt-3 flex flex-wrap gap-2">
                  {UNITS.map((u) => (
                    <button
                      key={u}
                      type="button"
                      onClick={() => setForm((f) => ({ ...f, quantity_unit: u }))}
                      className={`h-10 rounded-full border px-4 text-sm transition ${
                        form.quantity_unit === u
                          ? "border-lime-400 bg-lime-400 font-medium text-neutral-950"
                          : "border-white/15 text-white/70"
                      }`}
                    >
                      {t(`unit.${u}`, lang)}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-sm text-white/70">
                  {tr("farmer.origin")}
                </label>
                <input
                  value={form.origin_label}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, origin_label: e.target.value }))
                  }
                  className="h-12 w-full rounded-2xl border border-white/15 bg-neutral-900 px-4 text-base outline-none focus:border-lime-400"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="h-12 w-full rounded-full border border-lime-400 bg-lime-400 font-medium text-neutral-950 disabled:opacity-50"
              >
                {submitting ? tr("common.loading") : tr("farmer.submit")}
              </button>
            </form>
          </Card>
        )}
      </div>

      {/* Requests */}
      <h2 className="mb-3 text-lg font-medium">{tr("farmer.myRequests")}</h2>

      {error && (
        <ErrorState
          message={error.detail === "backend_unreachable"
            ? tr("common.backendDown") : error.message}
          onRetry={load}
          retryLabel={tr("common.retry")}
        />
      )}

      {loading && !error && <Loading label={tr("common.loading")} />}

      {!loading && !error && requests.length === 0 && (
        <EmptyState
          icon="🌾"
          title={tr("farmer.noRequests")}
          hint={tr("farmer.noRequests.hint")}
        />
      )}

      <div className="space-y-3">
        {requests.map((r) => (
          <Card key={r.request_id}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-lg font-medium">
                  {r.crop_label || r.crop_key}
                </p>
                <p className="mt-1 text-sm text-white/60">
                  {r.quantity_value} {t(`unit.${r.quantity_unit}`, lang)}
                  {r.quantity_kg != null && (
                    <span className="text-white/40">
                      {" "}· {r.quantity_kg.toLocaleString()} {t("unit.kg", lang)}
                    </span>
                  )}
                </p>
                {r.mandi_label && (
                  <p className="mt-0.5 text-sm text-white/40">→ {r.mandi_label}</p>
                )}
              </div>
              <StatusPill status={r.status} lang={lang} />
            </div>

            {/* The bori clarification path — the UI face of the Phase-A rule */}
            {r.needs_clarification && (
              <BoriPrompt
                request={r}
                lang={lang}
                onResolve={(kg) => resolveBori(r.request_id, kg)}
              />
            )}

            {!r.needs_clarification && r.status !== "DRAFT" && (
              <button
                onClick={() => router.push(`/app/farmer/route/${r.request_id}`)}
                className="mt-4 h-11 w-full rounded-full border border-white/20 text-sm transition hover:border-lime-400/50 sm:w-auto sm:px-6"
              >
                {tr("farmer.viewRoute")} →
              </button>
            )}
          </Card>
        ))}
      </div>
    </Shell>
  );
}

/** Asks for the bag weight rather than assuming one. */
function BoriPrompt({ request, lang, onResolve }) {
  const [kg, setKg] = useState("");
  const [busy, setBusy] = useState(false);

  return (
    <div className="mt-4 rounded-2xl border border-amber-500/25 bg-amber-500/5 p-4">
      <p className="text-sm text-amber-200">{request.clarification_prompt}</p>
      <div className="mt-3 flex flex-col gap-2 sm:flex-row">
        <input
          type="number"
          min="1"
          max="200"
          inputMode="decimal"
          placeholder={t("farmer.bagWeight", lang)}
          value={kg}
          onChange={(e) => setKg(e.target.value)}
          className="h-11 flex-1 rounded-full border border-white/15 bg-neutral-900 px-4 text-sm outline-none focus:border-amber-400"
        />
        <button
          disabled={!kg || busy}
          onClick={async () => {
            setBusy(true);
            await onResolve(kg);
            setBusy(false);
          }}
          className="h-11 rounded-full border border-amber-400 bg-amber-400 px-6 text-sm font-medium text-neutral-950 disabled:opacity-40"
        >
          {t("farmer.confirm", lang)}
        </button>
      </div>
    </div>
  );
}
