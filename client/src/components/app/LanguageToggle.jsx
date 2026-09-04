"use client";

/**
 * Hindi/English toggle.
 *
 * The choice lives in `SessionProvider` and persists to localStorage, so it
 * survives navigation and reloads and is the same setting everywhere — landing
 * page, sign-in, demo and the role dashboards.
 *
 * The button always shows the language you would switch *to*, which is the
 * convention users expect from a two-language toggle and avoids the ambiguity
 * of showing the current state.
 */

import { useSession } from "@/components/providers/SessionProvider";

export function LanguageToggle({ className = "" }) {
  const { lang, setLang } = useSession();
  const next = lang === "hi" ? "en" : "hi";

  return (
    <button
      onClick={() => setLang(next)}
      aria-label={lang === "hi" ? "Switch to English" : "हिंदी में बदलें"}
      title={lang === "hi" ? "Switch to English" : "हिंदी में बदलें"}
      className={
        "rounded-full border border-white/20 px-3 py-1.5 text-xs text-white/70 " +
        "transition hover:border-white/40 hover:text-white " + className
      }
    >
      {next === "en" ? "EN" : "हिं"}
    </button>
  );
}

export default LanguageToggle;
