/**
 * Hindi/English toggle.
 *
 * Two things matter beyond "the button exists":
 *
 *  1. **Dictionary parity.** A Hindi key with no English counterpart falls back
 *     to Hindi, which looks like a broken toggle rather than a missing string.
 *  2. **The choice persists.** A toggle that resets on navigation is worse than
 *     none, because the user re-does it on every page.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LanguageToggle } from "@/components/app/LanguageToggle";
import { SessionProvider } from "@/components/providers/SessionProvider";
import dict, { DEFAULT_LANGUAGE, LANGUAGES, t } from "@/lib/i18n";

const mockHealth = vi.fn();
vi.mock("@/lib/api", () => ({
  default: {
    health: (...a) => mockHealth(...a),
    devLogin: vi.fn(),
    me: vi.fn().mockResolvedValue({ user_id: "x", role: "FARMER", onboarded: true }),
  },
  apiFetch: vi.fn(),
  ApiError: class extends Error {},
}));

beforeEach(() => {
  mockHealth.mockResolvedValue({
    auth: { clerk_configured: false, dev_auth_active: true },
  });
});

describe("dictionary", () => {
  it("defaults to Hindi", () => {
    expect(DEFAULT_LANGUAGE).toBe("hi");
    expect(LANGUAGES).toEqual(["hi", "en"]);
  });

  it("every Hindi key has an English translation", () => {
    const missing = Object.keys(dict.hi).filter((k) => !(k in dict.en));
    expect(missing).toEqual([]);
  });

  it("every English key has a Hindi translation", () => {
    const missing = Object.keys(dict.en).filter((k) => !(k in dict.hi));
    expect(missing).toEqual([]);
  });

  it("no English value is left as Devanagari", () => {
    // A Hindi string sitting in the English dictionary means the toggle does
    // nothing for that key.
    const devanagari = /[ऀ-ॿ]/;
    const untranslated = Object.entries(dict.en)
      // app.name is the brand in Devanagari by design.
      .filter(([k, v]) => k !== "app.name" && devanagari.test(v))
      .map(([k]) => k);
    expect(untranslated).toEqual([]);
  });

  it("translates the landing page, not just the dashboards", () => {
    for (const k of ["landing.headline", "landing.sub", "landing.cta",
                     "nav.home", "intro.problem", "features.tag",
                     "footer.contact", "signup.tag"]) {
      expect(dict.hi[k]).toBeTruthy();
      expect(dict.en[k]).toBeTruthy();
      expect(dict.hi[k]).not.toBe(dict.en[k]);
    }
  });

  it("translates the auth and demo screens", () => {
    for (const k of ["auth.loginClerk", "auth.showDemo", "auth.realUser",
                     "demo.title", "demo.farmer.desc", "demo.trucker.desc",
                     "demo.dealer.desc"]) {
      expect(dict.hi[k]).toBeTruthy();
      expect(dict.en[k]).toBeTruthy();
    }
  });

  it("translates the map labels", () => {
    for (const k of ["map.realRoad", "map.outbound", "map.returnLoad",
                     "map.traffic", "map.estimate"]) {
      expect(dict.hi[k]).toBeTruthy();
      expect(dict.en[k]).toBeTruthy();
    }
  });
});

describe("LanguageToggle", () => {
  it("offers the language you would switch TO", async () => {
    render(
      <SessionProvider>
        <LanguageToggle />
      </SessionProvider>
    );
    // Default is Hindi, so the button offers EN.
    expect(await screen.findByRole("button", { name: /Switch to English/i }))
      .toBeInTheDocument();
  });

  it("switches to English and back", async () => {
    const user = userEvent.setup();
    render(
      <SessionProvider>
        <LanguageToggle />
      </SessionProvider>
    );
    const btn = await screen.findByRole("button");
    await user.click(btn);
    await waitFor(() =>
      expect(screen.getByRole("button")).toHaveTextContent("हिं"));
    await user.click(screen.getByRole("button"));
    await waitFor(() =>
      expect(screen.getByRole("button")).toHaveTextContent("EN"));
  });

  it("persists the choice so it survives navigation", async () => {
    const user = userEvent.setup();
    render(
      <SessionProvider>
        <LanguageToggle />
      </SessionProvider>
    );
    await user.click(await screen.findByRole("button"));
    await waitFor(() =>
      expect(window.localStorage.getItem("vb_lang")).toBe("en"));
  });
});

describe("t()", () => {
  it("returns the requested language", () => {
    expect(t("auth.showDemo", "hi")).toBe("डेमो देखें");
    expect(t("auth.showDemo", "en")).toBe("Show Demo");
  });

  it("falls back to Hindi for an unknown language", () => {
    expect(t("auth.showDemo", "de")).toBe(t("auth.showDemo", "hi"));
  });

  it("returns the key for an unknown string rather than blank", () => {
    expect(t("nope.nope", "en")).toBe("nope.nope");
  });
});
