"use client";

/**
 * Demo role selector.
 *
 * A separate journey from Clerk login, reached from `/signin` → Show Demo.
 * Clerk is never invoked here, and this page does not depend on Clerk being
 * configured.
 *
 * Each card enters using a seeded development identity. Those ids are an
 * implementation detail — the visitor picks an *experience*, not a username,
 * and never types an id.
 *
 * The backend still decides whether demo auth is permitted: `POST
 * /api/v1/auth/dev-login` returns 404 outside development. This page is a
 * convenience, not the security boundary.
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useSession } from "@/components/providers/SessionProvider";
import api from "@/lib/api";
import { t } from "@/lib/i18n";

const DEMOS = [
  {
    id: "dev_farmer_01",
    role: "FARMER",
    icon: "🌾",
    titleHi: "किसान",
    titleEn: "Farmer",
    descHi: "फसल भेजने का अनुरोध बनाएं, मंडी और मात्रा चुनें, और मिली हुई गाड़ी देखें।",
    descEn: "Create crop transport requests, choose mandi and quantity, and view matched transport.",
  },
  {
    id: "dev_trucker_01",
    role: "TRUCKER",
    icon: "🚚",
    titleHi: "ट्रक चालक",
    titleEn: "Trucker",
    descHi: "उपलब्ध काम, रास्ते, वापसी लोड और बचे हुए खाली किलोमीटर देखें।",
    descEn: "Explore jobs, routes, return loads and empty-kilometre savings.",
  },
  {
    id: "dev_dealer_01",
    role: "INPUT_DEALER",
    icon: "🏪",
    titleHi: "इनपुट डीलर",
    titleEn: "Input Dealer",
    descHi: "सामग्री की ज़रूरतें, आने वाली डिलीवरी और लौटती गाड़ियों के मौके देखें।",
    descEn: "Explore material requirements, incoming deliveries and returning-truck opportunities.",
  },
];

export default function DemoPage() {
  const { devSignIn, lang } = useSession();
  const router = useRouter();
  const [busy, setBusy] = useState(null);
  const [err, setErr] = useState(null);
  const [available, setAvailable] = useState(null);

  useEffect(() => {
    api
      .health()
      .then((h) => setAvailable(h?.auth?.dev_auth_active !== false))
      .catch(() => setAvailable(false));
  }, []);

  async function enter(d) {
    setBusy(d.id);
    setErr(null);
    try {
      await devSignIn(d.id, d.role);
      router.push("/app");
    } catch (e) {
      // Most likely the backend refused demo auth for this environment.
      setErr(
        e.status === 404
          ? lang === "hi"
            ? "इस वातावरण में डेमो प्रमाणीकरण उपलब्ध नहीं है।"
            : "Demo authentication is not available in this environment."
          : e.message
      );
      setBusy(null);
    }
  }

  return (
    <div className="min-h-screen bg-background px-4 py-10 text-foreground">
      <div className="mx-auto w-full max-w-2xl">
        <Link href="/" className="mb-8 flex items-center justify-center gap-2.5">
          <span className="grid h-10 w-10 place-items-center rounded-full bg-lime-400 text-base font-bold text-neutral-950">
            वा
          </span>
          <span className="text-xl font-medium">{t("app.name", lang)}</span>
        </Link>

        <h1 className="text-center text-2xl font-medium md:text-3xl">
          {lang === "hi" ? "वाहनबन्धु देखें" : "Explore VahaanBandhu"}
        </h1>
        <p className="mt-2 text-center text-sm text-white/50">
          {lang === "hi" ? "कोई एक अनुभव चुनें" : "Choose an experience"}
        </p>

        <div className="mx-auto mt-6 max-w-md rounded-2xl border border-amber-500/25 bg-amber-500/10 px-4 py-3 text-center text-xs text-amber-200">
          {lang === "hi"
            ? "डेमो मोड — नमूना डेटा। कोई असली खाता नहीं बनता।"
            : "Demo mode — sample data. No real account is created."}
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {DEMOS.map((d) => (
            <button
              key={d.id}
              onClick={() => enter(d)}
              disabled={Boolean(busy) || available === false}
              className="flex flex-col items-start gap-3 rounded-3xl border border-white/10 bg-neutral-900 p-6 text-left transition hover:border-lime-400/40 disabled:opacity-50 md:min-h-[230px]"
            >
              <span className="text-4xl">{d.icon}</span>
              <span className="text-lg font-medium">
                {lang === "hi" ? d.titleHi : d.titleEn}
              </span>
              <span className="flex-1 text-sm leading-relaxed text-white/50">
                {lang === "hi" ? d.descHi : d.descEn}
              </span>
              <span className="mt-1 flex items-center gap-2 text-sm text-lime-400">
                {busy === d.id ? (
                  <>
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-lime-400/30 border-t-lime-400" />
                    {t("common.loading", lang)}
                  </>
                ) : (
                  <>{lang === "hi" ? "शुरू करें" : "Start"} →</>
                )}
              </span>
            </button>
          ))}
        </div>

        {available === false && (
          <p className="mt-6 text-center text-sm text-white/45">
            {lang === "hi"
              ? "इस वातावरण में डेमो प्रमाणीकरण बंद है।"
              : "Demo authentication is disabled in this environment."}
          </p>
        )}

        {err && (
          <p className="mt-6 rounded-2xl border border-red-500/25 bg-red-500/5 px-4 py-3 text-center text-sm text-red-300">
            {err}
          </p>
        )}

        <Link
          href="/signin"
          className="mt-10 block text-center text-sm text-white/40 hover:text-white/70"
        >
          ← {lang === "hi" ? "लॉग इन पर वापस" : "Back to login"}
        </Link>
      </div>
    </div>
  );
}
