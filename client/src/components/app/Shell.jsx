"use client";

/**
 * Shared application shell.
 *
 * Holds the design language constant across all three roles — pure-black ground,
 * lime-400 accent, pill controls, rounded-3xl surfaces — while each role supplies
 * its own navigation. Shared primitives, distinct experiences.
 *
 * Mobile-first: navigation is a bottom bar on small screens (thumb-reachable,
 * large targets) and a top bar from `md` up. Rural users are on phones.
 */

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useSession } from "@/components/providers/SessionProvider";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export function Shell({ nav = [], title, children }) {
  const { lang, setLang, user, signOut, role } = useSession();
  const pathname = usePathname();
  const router = useRouter();

  // The public deployment has no backend, so the app serves a bundled snapshot.
  // Say so plainly rather than letting a read-only snapshot look live.
  const [staticDemo, setStaticDemo] = useState(false);
  useEffect(() => {
    const onStatic = () => setStaticDemo(true);
    window.addEventListener("vb:static-demo", onStatic);
    return () => window.removeEventListener("vb:static-demo", onStatic);
  }, []);
  const tr = (k) => t(k, lang);

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Top bar */}
      <header className="sticky top-0 z-40 border-b border-white/10 bg-neutral-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
          <Link href="/app" className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-full bg-lime-400 text-sm font-bold text-neutral-950">
              वा
            </span>
            <span className="hidden text-base font-medium sm:block">
              {tr("app.name")}
            </span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden items-center gap-1 md:flex">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-full px-4 py-2 text-sm transition",
                  pathname === item.href
                    ? "bg-lime-400 text-neutral-950 font-medium"
                    : "text-white/70 hover:text-white hover:bg-white/5"
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setLang(lang === "hi" ? "en" : "hi")}
              className="rounded-full border border-white/15 px-3 py-1.5 text-xs text-white/70 transition hover:text-white"
              aria-label="Toggle language"
            >
              {lang === "hi" ? "EN" : "हिं"}
            </button>
            {user && (
              <button
                onClick={signOut}
                className="rounded-full border border-white/15 px-3 py-1.5 text-xs text-white/70 transition hover:border-white/30 hover:text-white"
              >
                {tr("nav.signOut")}
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Demo-mode banner. Development only, and unmistakable.
          Carries its own exit so a visitor never has to clear local storage
          by hand to leave demo mode. */}
      {user?.auth_source === "dev" && (
        <div className="flex items-center justify-center gap-3 border-b border-amber-500/25 bg-amber-500/10 px-4 py-1.5 text-center text-xs text-amber-200">
          <span>
            {tr("common.demoMode")} · {role}
            {staticDemo && (
              <span className="ml-2 text-amber-300/80">
                {lang === "hi"
                  ? "· नमूना डेटा (केवल पढ़ने के लिए)"
                  : "· sample data (read-only)"}
              </span>
            )}
          </span>
          <button
            onClick={() => {
              signOut();
              router.push("/signin");
            }}
            className="rounded-full border border-amber-400/40 px-2.5 py-0.5 text-[11px] text-amber-100 transition hover:bg-amber-400/15"
          >
            {lang === "hi" ? "डेमो से बाहर" : "Exit demo"}
          </button>
        </div>
      )}

      <main className="mx-auto max-w-6xl px-4 pb-28 pt-6 md:pb-12">
        {title && (
          <h1 className="mb-6 text-2xl font-medium md:text-3xl">{title}</h1>
        )}
        {children}
      </main>

      {/* Mobile bottom nav: large targets, thumb-reachable */}
      {nav.length > 0 && (
        <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-white/10 bg-neutral-950/95 backdrop-blur md:hidden">
          <div className="flex items-stretch justify-around">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex min-h-[60px] flex-1 flex-col items-center justify-center gap-1 px-2 py-2 text-[11px] transition",
                  pathname === item.href
                    ? "text-lime-400"
                    : "text-white/55 hover:text-white"
                )}
              >
                <span className="text-lg leading-none">{item.icon}</span>
                <span className="text-center leading-tight">{item.label}</span>
              </Link>
            ))}
          </div>
        </nav>
      )}
    </div>
  );
}

/** Standard surface card. rounded-3xl + neutral-900, per the design language. */
export function Card({ className, children, ...props }) {
  return (
    <div
      className={cn(
        "rounded-3xl border border-white/10 bg-neutral-900 p-5",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

/** Section eyebrow tag — lime outline, uppercase, pill. */
export function Tag({ children, className }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full border border-lime-400 px-3 py-1 text-xs uppercase tracking-wide text-lime-400",
        className
      )}
    >
      {children}
    </span>
  );
}

export function StatusPill({ status, lang = "hi" }) {
  const tone =
    {
      COMPLETED: "bg-lime-400/15 text-lime-300 border-lime-400/30",
      DELIVERED: "bg-lime-400/15 text-lime-300 border-lime-400/30",
      CANCELLED: "bg-red-500/10 text-red-300 border-red-500/30",
      DRAFT: "bg-amber-500/10 text-amber-300 border-amber-500/30",
    }[status] || "bg-white/5 text-white/70 border-white/15";

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-3 py-1 text-xs",
        tone
      )}
    >
      {t(`status.${status}`, lang)}
    </span>
  );
}

/** Empty state. Never a blank panel. */
export function EmptyState({ icon = "○", title, hint, action }) {
  return (
    <div className="rounded-3xl border border-dashed border-white/15 bg-neutral-900/50 px-6 py-14 text-center">
      <div className="mb-3 text-3xl text-white/25">{icon}</div>
      <p className="text-white/70">{title}</p>
      {hint && <p className="mt-1 text-sm text-white/40">{hint}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function Loading({ label }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-white/50">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-lime-400" />
      <span className="text-sm">{label}</span>
    </div>
  );
}

/** Error state with a retry affordance — never a white screen. */
export function ErrorState({ message, onRetry, retryLabel = "फिर कोशिश करें" }) {
  return (
    <div className="rounded-3xl border border-red-500/25 bg-red-500/5 px-6 py-10 text-center">
      <div className="mb-2 text-2xl">⚠</div>
      <p className="text-white/80">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 rounded-full border border-white/20 px-5 py-2 text-sm transition hover:border-white/40"
        >
          {retryLabel}
        </button>
      )}
    </div>
  );
}
