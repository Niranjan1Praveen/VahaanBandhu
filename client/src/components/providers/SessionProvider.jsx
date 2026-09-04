"use client";

/**
 * Session context.
 *
 * Bridges two auth paths behind one interface:
 *
 *  - **Clerk** (production). When configured, the Clerk session token is
 *    attached to API calls as a bearer.
 *  - **Development sign-in** (local only). When Clerk is not configured, a
 *    seeded demo user is selected and identified by `x-dev-user`.
 *
 * In both cases the **role comes from the backend**, never from this component.
 * The frontend renders what the server says the user is; it does not assert it.
 * Route protection here is a UX affordance — the real enforcement is server-side.
 */

import { createContext, useCallback, useContext, useEffect, useState } from "react";

import api, { ApiError } from "@/lib/api";
import { DEFAULT_LANGUAGE } from "@/lib/i18n";

const SessionContext = createContext(null);

const DEV_USER_KEY = "vb_dev_user";
const LANG_KEY = "vb_lang";

export function SessionProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | authed | anon | error
  const [error, setError] = useState(null);
  const [lang, setLangState] = useState(DEFAULT_LANGUAGE);

  const refresh = useCallback(async () => {
    if (typeof window === "undefined") return;
    const dev = window.localStorage.getItem(DEV_USER_KEY);
    if (!dev) {
      setUser(null);
      setStatus("anon");
      return;
    }
    try {
      const me = await api.me();
      setUser(me);
      setStatus("authed");
      setError(null);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        // A stale dev identity: clear it rather than looping on 401s.
        window.localStorage.removeItem(DEV_USER_KEY);
        setUser(null);
        setStatus("anon");
      } else {
        setError(e);
        setStatus("error");
      }
    }
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = window.localStorage.getItem(LANG_KEY);
      if (saved) setLangState(saved);
    }
    refresh();
  }, [refresh]);

  const devSignIn = useCallback(
    async (userId, role) => {
      window.localStorage.setItem(DEV_USER_KEY, userId);
      await api.devLogin({ user_id: userId, role: role || undefined });
      await refresh();
    },
    [refresh]
  );

  const signOut = useCallback(() => {
    window.localStorage.removeItem(DEV_USER_KEY);
    setUser(null);
    setStatus("anon");
  }, []);

  const selectRole = useCallback(
    async (payload) => {
      const updated = await api.selectRole(payload);
      setUser(updated);
      return updated;
    },
    []
  );

  const setLang = useCallback((next) => {
    setLangState(next);
    if (typeof window !== "undefined") window.localStorage.setItem(LANG_KEY, next);
  }, []);

  return (
    <SessionContext.Provider
      value={{
        user,
        status,
        error,
        lang,
        setLang,
        role: user?.role ?? null,
        onboarded: Boolean(user?.onboarded),
        refresh,
        devSignIn,
        signOut,
        selectRole,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used inside SessionProvider");
  return ctx;
}
