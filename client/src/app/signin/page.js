"use client";

/**
 * Entry screen — two architecturally distinct journeys.
 *
 *   1. Login with Clerk  → real authentication, real user profile, real role
 *   2. Show Demo         → /demo role selector, seeded development identities
 *
 * These are deliberately NOT the same path with a fallback. An earlier version
 * showed the demo list *because* Clerk was unconfigured, which conflated
 * "no credentials here" with "this visitor wants a demo". They are different
 * questions.
 *
 * Consequences held to:
 *   - Show Demo never invokes Clerk and never depends on Clerk availability.
 *   - Clerk login never silently degrades into demo auth. Unconfigured Clerk
 *     produces an honest message, not a redirect.
 *   - Demo auth is validated by the backend, not merely gated in the browser.
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useSession } from "@/components/providers/SessionProvider";
import api from "@/lib/api";
import { t } from "@/lib/i18n";

export default function SignInPage() {
  const { lang, status, user } = useSession();
  const router = useRouter();
  const [health, setHealth] = useState(null);
  const [clerkMessage, setClerkMessage] = useState(null);
  const tr = (k) => t(k, lang);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ auth: {} }));
  }, []);

  useEffect(() => {
    if (status === "authed" && user) {
      router.replace(user.onboarded ? "/app" : "/app/role");
    }
  }, [status, user, router]);

  const clerkConfigured = Boolean(health?.auth?.clerk_configured);
  const demoAvailable = health?.auth?.dev_auth_active !== false;

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-10 text-foreground">
      <div className="w-full max-w-md">
        <Link href="/" className="mb-10 flex items-center justify-center gap-2.5">
          <span className="grid h-11 w-11 place-items-center rounded-full bg-lime-400 text-lg font-bold text-neutral-950">
            वा
          </span>
          <span className="text-2xl font-medium">{tr("app.name")}</span>
        </Link>

        <p className="mb-10 text-center text-sm text-white/50">
          {tr("app.tagline")}
        </p>

        {/* ---------- 1. Real authentication ---------- */}
        <p className="mb-2.5 text-center text-sm text-white/60">
          {lang === "hi" ? "असली उपयोगकर्ता?" : "Real user?"}
        </p>
        <Link
          href={clerkConfigured ? "/sign-in" : "#"}
          onClick={(e) => {
            if (!clerkConfigured) {
              e.preventDefault();
              // Honest message. Never a silent downgrade to demo auth.
              setClerkMessage(
                lang === "hi"
                  ? "इस स्थानीय वातावरण में Clerk प्रमाणीकरण कॉन्फ़िगर नहीं है।"
                  : "Clerk authentication is not configured for this local environment."
              );
            }
          }}
          className={`flex h-14 w-full items-center justify-center gap-3 rounded-full border text-base font-medium transition ${
            clerkConfigured
              ? "border-lime-400 bg-lime-400 text-neutral-950 active:scale-[0.99]"
              : "border-lime-400/35 bg-lime-400/10 text-lime-200/80"
          }`}
        >
          <span>🔐</span>
          {lang === "hi" ? "Clerk से लॉग इन करें" : "Login with Clerk"}
        </Link>

        {clerkMessage && (
          <p className="mt-3 rounded-2xl border border-amber-500/25 bg-amber-500/5 px-4 py-3 text-center text-sm text-amber-200">
            {clerkMessage}
          </p>
        )}

        {/* ---------- divider ---------- */}
        <div className="my-8 flex items-center gap-4">
          <span className="h-px flex-1 bg-white/10" />
          <span className="text-xs uppercase tracking-wider text-white/25">
            {lang === "hi" ? "या" : "or"}
          </span>
          <span className="h-px flex-1 bg-white/10" />
        </div>

        {/* ---------- 2. Demo ---------- */}
        <p className="mb-2.5 text-center text-sm text-white/60">
          {lang === "hi" ? "पहले देखना चाहते हैं?" : "Want to explore first?"}
        </p>
        <Link
          href="/demo"
          aria-disabled={!demoAvailable}
          className={`flex h-14 w-full items-center justify-center gap-3 rounded-full border text-base font-medium transition ${
            demoAvailable
              ? "border-white text-white active:scale-[0.99] hover:bg-white/5"
              : "pointer-events-none border-white/15 text-white/30"
          }`}
        >
          <span>👁️</span>
          {lang === "hi" ? "डेमो देखें" : "Show Demo"}
        </Link>

        {!demoAvailable && (
          <p className="mt-3 text-center text-xs text-white/35">
            {lang === "hi"
              ? "इस वातावरण में डेमो उपलब्ध नहीं है।"
              : "The demo is not available in this environment."}
          </p>
        )}

        {health === null && (
          <div className="mt-10 flex justify-center">
            <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/20 border-t-lime-400" />
          </div>
        )}

        <Link
          href="/"
          className="mt-10 block text-center text-sm text-white/40 hover:text-white/70"
        >
          ← {lang === "hi" ? "मुख्य पृष्ठ" : "Home"}
        </Link>
      </div>
    </div>
  );
}
