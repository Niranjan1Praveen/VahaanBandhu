"use client";

/**
 * Role onboarding.
 *
 * Two steps, deliberately: pick a role, then answer only the questions that role
 * actually needs. A single long form for all three roles is how rural onboarding
 * gets abandoned.
 *
 * The role is persisted server-side; nothing here is trusted by the API.
 */

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useSession } from "@/components/providers/SessionProvider";
import { t } from "@/lib/i18n";

const ROLES = [
  { key: "FARMER", icon: "🌾", labelKey: "role.farmer", descKey: "role.farmer.desc" },
  { key: "TRUCKER", icon: "🚛", labelKey: "role.trucker", descKey: "role.trucker.desc" },
  { key: "INPUT_DEALER", icon: "🏪", labelKey: "role.dealer", descKey: "role.dealer.desc" },
];

// Only the fields each role genuinely needs.
const FIELDS = {
  FARMER: [
    { name: "display_name", hi: "आपका नाम", en: "Your name" },
    { name: "village", hi: "गाँव", en: "Village" },
    { name: "district", hi: "ज़िला", en: "District" },
  ],
  TRUCKER: [
    { name: "display_name", hi: "आपका नाम", en: "Your name" },
    { name: "vehicle_number", hi: "गाड़ी नंबर", en: "Vehicle number" },
    { name: "capacity_kg", hi: "क्षमता (किलो)", en: "Capacity (kg)", type: "number" },
    { name: "district", hi: "ज़िला", en: "District" },
  ],
  INPUT_DEALER: [
    { name: "business_name", hi: "दुकान का नाम", en: "Shop name" },
    { name: "display_name", hi: "आपका नाम", en: "Your name" },
    { name: "district", hi: "ज़िला", en: "District" },
  ],
};

export default function RolePage() {
  const { lang, selectRole, status } = useSession();
  const router = useRouter();
  const [role, setRole] = useState(null);
  const [values, setValues] = useState({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const tr = (k) => t(k, lang);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      const payload = { role, ...values };
      if (payload.capacity_kg) payload.capacity_kg = Number(payload.capacity_kg);
      await selectRole(payload);
      router.push("/app");
    } catch (e2) {
      setErr(e2.message);
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-background px-4 py-10 text-foreground">
      <div className="mx-auto w-full max-w-lg">
        <h1 className="text-center text-3xl font-medium">{tr("role.question")}</h1>
        <p className="mt-2 text-center text-sm text-white/50">
          {tr("role.subtitle")}
        </p>

        {/* Step 1 — pick a role */}
        <div className="mt-8 space-y-3">
          {ROLES.map((r) => (
            <button
              key={r.key}
              onClick={() => setRole(r.key)}
              className={`flex w-full items-center gap-4 rounded-3xl border p-5 text-left transition ${
                role === r.key
                  ? "border-lime-400 bg-lime-400/10"
                  : "border-white/10 bg-neutral-900 hover:border-white/25"
              }`}
            >
              <span className="text-3xl">{r.icon}</span>
              <span className="flex-1">
                <span className="block text-lg font-medium">{tr(r.labelKey)}</span>
                <span className="mt-0.5 block text-sm text-white/50">
                  {tr(r.descKey)}
                </span>
              </span>
              <span
                className={`grid h-6 w-6 place-items-center rounded-full border ${
                  role === r.key
                    ? "border-lime-400 bg-lime-400 text-neutral-950"
                    : "border-white/25"
                }`}
              >
                {role === r.key ? "✓" : ""}
              </span>
            </button>
          ))}
        </div>

        {/* Step 2 — only this role's fields */}
        {role && (
          <form onSubmit={submit} className="mt-8 space-y-4">
            {FIELDS[role].map((f) => (
              <div key={f.name}>
                <label className="mb-1.5 block text-sm text-white/70">
                  {lang === "hi" ? f.hi : f.en}
                </label>
                <input
                  type={f.type || "text"}
                  value={values[f.name] || ""}
                  onChange={(e) =>
                    setValues((v) => ({ ...v, [f.name]: e.target.value }))
                  }
                  className="h-12 w-full rounded-2xl border border-white/15 bg-neutral-900 px-4 text-base outline-none transition focus:border-lime-400"
                />
              </div>
            ))}

            {err && (
              <p className="rounded-2xl border border-red-500/25 bg-red-500/5 px-4 py-3 text-sm text-red-300">
                {err}
              </p>
            )}

            <button
              type="submit"
              disabled={busy}
              className="h-12 w-full rounded-full border border-lime-400 bg-lime-400 font-medium text-neutral-950 transition disabled:opacity-50"
            >
              {busy ? tr("common.loading") : tr("role.continue")}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
