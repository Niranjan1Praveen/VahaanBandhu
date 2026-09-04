"use client";

/**
 * Sign in.
 *
 * Renders the Clerk flow when Clerk is configured. Otherwise it offers the
 * development sign-in, which is unmistakably labelled as such — it exists so
 * local UI work and screenshots do not depend on network access to Clerk, and
 * the backend refuses it outside development.
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useSession } from "@/components/providers/SessionProvider";
import api from "@/lib/api";
import { t } from "@/lib/i18n";

const DEMO_USERS = [
  {
    id: "dev_farmer_01",
    role: "FARMER",
    icon: "🌾",
    nameHi: "किसान — रमेश कुमार",
    nameEn: "Farmer — Ramesh Kumar",
  },
  {
    id: "dev_trucker_01",
    role: "TRUCKER",
    icon: "🚛",
    nameHi: "ट्रक चालक — सुखबीर सिंह",
    nameEn: "Trucker — Sukhbir Singh",
  },
  {
    id: "dev_dealer_01",
    role: "INPUT_DEALER",
    icon: "🏪",
    nameHi: "इनपुट डीलर — श्री बालाजी",
    nameEn: "Input dealer — Shri Balaji",
  },
];

export default function SignInPage() {
  const { devSignIn, lang, status, user } = useSession();
  const router = useRouter();
  const [busy, setBusy] = useState(null);
  const [clerkConfigured, setClerkConfigured] = useState(null);
  const [err, setErr] = useState(null);
  const tr = (k) => t(k, lang);

  useEffect(() => {
    api
      .health()
      .then((h) => setClerkConfigured(Boolean(h?.auth?.clerk_configured)))
      .catch(() => setClerkConfigured(false));
  }, []);

  useEffect(() => {
    if (status === "authed" && user) {
      router.replace(user.onboarded ? "/app" : "/app/role");
    }
  }, [status, user, router]);

  async function handleDemo(u) {
    setBusy(u.id);
    setErr(null);
    try {
      await devSignIn(u.id, u.role);
      router.push("/app");
    } catch (e) {
      setErr(e.message);
      setBusy(null);
    }
  }

  return (
    <div className="min-h-screen bg-background px-4 py-10 text-foreground">
      <div className="mx-auto w-full max-w-md">
        <Link href="/" className="mb-8 flex items-center justify-center gap-2">
          <span className="grid h-10 w-10 place-items-center rounded-full bg-lime-400 text-base font-bold text-neutral-950">
            वा
          </span>
          <span className="text-xl font-medium">{tr("app.name")}</span>
        </Link>

        <h1 className="text-center text-2xl font-medium">{tr("nav.signIn")}</h1>
        <p className="mt-2 text-center text-sm text-white/50">
          {tr("app.tagline")}
        </p>

        {clerkConfigured === true && (
          <div className="mt-8 rounded-3xl border border-white/10 bg-neutral-900 p-6 text-center">
            <p className="text-sm text-white/70">
              Clerk is configured. Continue with your account.
            </p>
            <Link
              href="/sign-in"
              className="mt-4 inline-flex h-12 items-center rounded-full border border-lime-400 bg-lime-400 px-6 font-medium text-neutral-950"
            >
              {tr("nav.signIn")}
            </Link>
          </div>
        )}

        {clerkConfigured === false && (
          <div className="mt-8">
            <div className="mb-4 rounded-2xl border border-amber-500/25 bg-amber-500/10 px-4 py-3 text-center text-xs text-amber-200">
              {lang === "hi"
                ? "डेमो मोड — केवल स्थानीय विकास के लिए"
                : "Demo mode — local development only"}
            </div>

            <div className="space-y-3">
              {DEMO_USERS.map((u) => (
                <button
                  key={u.id}
                  onClick={() => handleDemo(u)}
                  disabled={Boolean(busy)}
                  className="flex w-full items-center gap-4 rounded-3xl border border-white/10 bg-neutral-900 p-5 text-left transition hover:border-lime-400/40 disabled:opacity-50"
                >
                  <span className="text-3xl">{u.icon}</span>
                  <span className="flex-1">
                    <span className="block font-medium">
                      {lang === "hi" ? u.nameHi : u.nameEn}
                    </span>
                    <span className="mt-0.5 block text-xs text-white/40">
                      {u.id}
                    </span>
                  </span>
                  {busy === u.id && (
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-lime-400" />
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {clerkConfigured === null && (
          <div className="mt-10 flex justify-center">
            <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/20 border-t-lime-400" />
          </div>
        )}

        {err && (
          <p className="mt-5 rounded-2xl border border-red-500/25 bg-red-500/5 px-4 py-3 text-center text-sm text-red-300">
            {err}
          </p>
        )}

        <Link
          href="/"
          className="mt-8 block text-center text-sm text-white/40 hover:text-white/70"
        >
          ← {lang === "hi" ? "मुख्य पृष्ठ" : "Home"}
        </Link>
      </div>
    </div>
  );
}
