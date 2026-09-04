"use client";

/**
 * Input dealer experience.
 *
 * A dealer's mental model is stock, not routes: what have I ordered, what is on
 * its way, when does it arrive. The information hierarchy reflects that —
 * incoming deliveries sit above the requirement list, and route detail is
 * deliberately absent.
 */

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  Card, EmptyState, ErrorState, Loading, Shell, StatusPill, Tag,
} from "@/components/app/Shell";
import { useSession } from "@/components/providers/SessionProvider";
import api from "@/lib/api";
import { t } from "@/lib/i18n";

const MATERIAL_LABELS = {
  cement: "सीमेंट", tmt: "स्टील / टीएमटी", brick: "ईंट", hardware: "हार्डवेयर",
  pipe: "पाइप", electrical: "इलेक्ट्रिकल", paint: "पेंट", tile: "टाइल्स",
  sanitary: "सैनिटरी", roofing: "रूफिंग", multi: "मिश्रित", agri_input: "कृषि इनपुट",
};

const UNITS = ["kg", "tonne", "bori"];

export default function DealerPage() {
  const { lang, status } = useSession();
  const router = useRouter();
  const tr = (k) => t(k, lang);

  const [materials, setMaterials] = useState([]);
  const [requirements, setRequirements] = useState([]);
  const [incoming, setIncoming] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    material: "", quantity_value: "", quantity_unit: "kg",
    delivery_label: "", needed_by: "",
  });

  const nav = [
    { href: "/app/dealer", label: tr("nav.dashboard"), icon: "🏠" },
    { href: "/app/map", label: tr("route.title"), icon: "🗺️" },
  ];

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [m, r, i] = await Promise.all([
        api.dealer.materials(),
        api.dealer.listRequirements(),
        api.dealer.incoming(),
      ]);
      setMaterials(m.materials || []);
      setRequirements(r || []);
      setIncoming(i || []);
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
      await api.dealer.createRequirement({
        material: form.material,
        material_label: MATERIAL_LABELS[form.material] || form.material,
        quantity_value: Number(form.quantity_value),
        quantity_unit: form.quantity_unit,
        delivery_label: form.delivery_label,
        needed_by: form.needed_by || null,
        // Sonipat-area delivery point so return-load matching has geometry.
        delivery_point: { latitude: 28.96, longitude: 76.85 },
      });
      setShowForm(false);
      setForm({
        material: "", quantity_value: "", quantity_unit: "kg",
        delivery_label: "", needed_by: "",
      });
      await load();
    } catch (e2) {
      setError(e2);
    } finally {
      setSubmitting(false);
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
    <Shell nav={nav} title={tr("dealer.title")}>
      <div className="mb-6">
        {!showForm ? (
          <button
            onClick={() => setShowForm(true)}
            className="h-14 w-full rounded-full border border-lime-400 bg-lime-400 text-base font-medium text-neutral-950 transition active:scale-[0.99]"
          >
            + {tr("dealer.newRequirement")}
          </button>
        ) : (
          <Card>
            <div className="mb-4 flex items-center justify-between">
              <Tag>{tr("dealer.newRequirement")}</Tag>
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
                  {tr("dealer.material")}
                </label>
                <div className="flex flex-wrap gap-2">
                  {materials.map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setForm((f) => ({ ...f, material: m }))}
                      className={`h-10 rounded-full border px-4 text-sm transition ${
                        form.material === m
                          ? "border-lime-400 bg-lime-400 font-medium text-neutral-950"
                          : "border-white/15 text-white/70"
                      }`}
                    >
                      {MATERIAL_LABELS[m] || m}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-sm text-white/70">
                  {tr("dealer.quantity")}
                </label>
                <input
                  required
                  type="number"
                  min="1"
                  inputMode="decimal"
                  value={form.quantity_value}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, quantity_value: e.target.value }))
                  }
                  className="h-12 w-full rounded-2xl border border-white/15 bg-neutral-900 px-4 text-base outline-none focus:border-lime-400"
                />
                <div className="mt-3 flex gap-2">
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
                  {tr("dealer.deliveryLocation")}
                </label>
                <input
                  value={form.delivery_label}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, delivery_label: e.target.value }))
                  }
                  className="h-12 w-full rounded-2xl border border-white/15 bg-neutral-900 px-4 text-base outline-none focus:border-lime-400"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm text-white/70">
                  {tr("dealer.neededBy")}
                </label>
                <input
                  type="date"
                  value={form.needed_by}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, needed_by: e.target.value }))
                  }
                  className="h-12 w-full rounded-2xl border border-white/15 bg-neutral-900 px-4 text-base outline-none focus:border-lime-400"
                />
              </div>

              <button
                type="submit"
                disabled={submitting || !form.material}
                className="h-12 w-full rounded-full border border-lime-400 bg-lime-400 font-medium text-neutral-950 disabled:opacity-50"
              >
                {submitting ? tr("common.loading") : tr("dealer.submit")}
              </button>
            </form>
          </Card>
        )}
      </div>

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

      {/* Incoming first: what a dealer actually wants to know */}
      {incoming.length > 0 && (
        <section className="mb-6">
          <h2 className="mb-3 text-lg font-medium">{tr("dealer.incoming")}</h2>
          <div className="space-y-3">
            {incoming.map((r) => (
              <Card key={r.requirement_id} className="border-lime-400/25">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-medium">{r.material_label || r.material}</p>
                    <p className="mt-1 text-sm text-white/50">
                      {r.quantity_kg?.toLocaleString()} {t("unit.kg", lang)}
                    </p>
                  </div>
                  <StatusPill status={r.status} lang={lang} />
                </div>
              </Card>
            ))}
          </div>
        </section>
      )}

      <h2 className="mb-3 text-lg font-medium">{tr("dealer.myRequirements")}</h2>

      {loading && <Loading label={tr("common.loading")} />}

      {!loading && requirements.length === 0 && (
        <EmptyState icon="🏪" title={tr("dealer.noRequirements")} />
      )}

      <div className="space-y-3">
        {requirements.map((r) => (
          <Card key={r.requirement_id}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-lg font-medium">
                  {r.material_label || r.material}
                </p>
                <p className="mt-1 text-sm text-white/60">
                  {r.quantity_value} {t(`unit.${r.quantity_unit}`, lang)}
                  {r.quantity_kg != null && (
                    <span className="text-white/40">
                      {" "}· {r.quantity_kg.toLocaleString()} {t("unit.kg", lang)}
                    </span>
                  )}
                </p>
                {r.delivery_label && (
                  <p className="mt-0.5 text-sm text-white/40">{r.delivery_label}</p>
                )}
                {r.needed_by && (
                  <p className="mt-0.5 text-xs text-white/35">→ {r.needed_by}</p>
                )}
              </div>
              <StatusPill status={r.status} lang={lang} />
            </div>

            {r.needs_clarification && (
              <p className="mt-4 rounded-2xl border border-amber-500/25 bg-amber-500/5 p-3 text-sm text-amber-200">
                {r.clarification_prompt}
              </p>
            )}
          </Card>
        ))}
      </div>
    </Shell>
  );
}
