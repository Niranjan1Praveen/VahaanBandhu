/**
 * Role experiences and API-failure behaviour.
 *
 * Two things are worth testing here beyond "it renders":
 *
 *  1. **The bori rule surfaces in the UI.** The backend refuses to guess a
 *     kilogram figure; the farmer dashboard must actually show the resulting
 *     clarification prompt rather than rendering a blank or a zero.
 *  2. **A failing API never produces a blank screen.** Every dashboard must
 *     show an error state with a retry, because rural connectivity is the
 *     normal case, not the edge case.
 */

import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { t } from "@/lib/i18n";

const api = {
  health: vi.fn(),
  me: vi.fn(),
  crops: vi.fn(),
  mandis: vi.fn(),
  farmer: { listRequests: vi.fn(), createRequest: vi.fn(), resolveQuantity: vi.fn() },
  trucker: { vehicles: vi.fn(), jobs: vi.fn(), myJobs: vi.fn(), returnLoads: vi.fn() },
  dealer: { materials: vi.fn(), listRequirements: vi.fn(), incoming: vi.fn() },
};

vi.mock("@/lib/api", () => ({
  default: api,
  apiFetch: vi.fn(),
  ApiError: class ApiError extends Error {
    constructor(m, status, detail) {
      super(m);
      this.status = status;
      this.detail = detail;
    }
  },
}));

vi.mock("@/components/providers/SessionProvider", async () => {
  const actual = await vi.importActual("@/components/providers/SessionProvider");
  return {
    ...actual,
    useSession: () => ({
      lang: "hi",
      setLang: vi.fn(),
      status: "authed",
      user: { user_id: "dev_farmer_01", role: "FARMER", auth_source: "dev" },
      role: "FARMER",
      signOut: vi.fn(),
      refresh: vi.fn(),
    }),
  };
});

beforeEach(() => {
  api.me.mockResolvedValue({ user_id: "dev_farmer_01", role: "FARMER", onboarded: true });
  api.crops.mockResolvedValue({ results: [
    { crop_key: "wheat", name_hi: "गेहूँ", name_en: "Wheat" },
    { crop_key: "sugarcane", name_hi: "गन्ना", name_en: "Sugarcane" },
  ]});
  api.mandis.mockResolvedValue({ results: [
    { mandi_id: "MND_1", name_hi: "सोनीपत मंडी", district: "Sonipat" },
  ]});
  api.farmer.listRequests.mockResolvedValue([]);
  api.trucker.vehicles.mockResolvedValue([]);
  api.trucker.jobs.mockResolvedValue([]);
  api.trucker.myJobs.mockResolvedValue([]);
  api.trucker.returnLoads.mockResolvedValue([]);
  api.dealer.materials.mockResolvedValue({ materials: ["cement", "tmt"] });
  api.dealer.listRequirements.mockResolvedValue([]);
  api.dealer.incoming.mockResolvedValue([]);
});

describe("farmer dashboard", () => {
  it("shows the bori clarification prompt when the backend cannot convert",
    async () => {
      const { default: FarmerPage } = await import("@/app/app/farmer/page");
      api.farmer.listRequests.mockResolvedValue([{
        request_id: "REQ_1",
        status: "DRAFT",
        crop_key: "sugarcane",
        crop_label: "गन्ना",
        quantity_value: 15,
        quantity_unit: "bori",
        // The backend refused to guess. This is the whole point.
        quantity_kg: null,
        conversion_confidence: "unresolved",
        needs_clarification: true,
        clarification_prompt: "एक बोरी का वज़न फसल के अनुसार बदलता है।",
        status_history: [],
      }]);

      render(<FarmerPage />);
      expect(await screen.findByText(/एक बोरी का वज़न/)).toBeInTheDocument();
    });

  it("does not invent a kilogram figure for an unresolved quantity", async () => {
    const { default: FarmerPage } = await import("@/app/app/farmer/page");
    api.farmer.listRequests.mockResolvedValue([{
      request_id: "REQ_1", status: "DRAFT", crop_key: "sugarcane",
      crop_label: "गन्ना", quantity_value: 15, quantity_unit: "bori",
      quantity_kg: null, conversion_confidence: "unresolved",
      needs_clarification: true, clarification_prompt: "…", status_history: [],
    }]);
    render(<FarmerPage />);
    await screen.findByText("गन्ना");
    // 15 bori x 50 kg would be 750. It must not appear.
    expect(screen.queryByText(/750/)).not.toBeInTheDocument();
  });

  it("shows the resolved kilogram figure when the backend could convert",
    async () => {
      const { default: FarmerPage } = await import("@/app/app/farmer/page");
      api.farmer.listRequests.mockResolvedValue([{
        request_id: "REQ_2", status: "REQUESTED", crop_key: "wheat",
        crop_label: "गेहूँ", quantity_value: 25, quantity_unit: "quintal",
        quantity_kg: 2500, conversion_confidence: "exact",
        needs_clarification: false, status_history: [],
      }]);
      render(<FarmerPage />);
      expect(await screen.findByText(/2,500/)).toBeInTheDocument();
    });

  it("shows an empty state rather than a blank panel", async () => {
    const { default: FarmerPage } = await import("@/app/app/farmer/page");
    render(<FarmerPage />);
    await waitFor(() =>
      expect(document.body.textContent).toContain("कोई अनुरोध नहीं"));
  });

  it("renders an error state with a retry when the API is unreachable",
    async () => {
      const { default: FarmerPage } = await import("@/app/app/farmer/page");
      const { ApiError } = await import("@/lib/api");
      api.farmer.listRequests.mockRejectedValue(
        new ApiError("down", 0, "backend_unreachable"));
      render(<FarmerPage />);
      await waitFor(() =>
        expect(document.body.textContent).toContain("सर्वर उपलब्ध नहीं"));
      // The retry affordance must exist -- an error with no way forward is a
      // dead end on a rural connection.
      expect(document.body.textContent).toContain("फिर कोशिश करें");
    });
});

describe("i18n", () => {
  it("has Hindi for every key used by the shell", () => {
    for (const k of ["app.name", "nav.dashboard", "common.loading",
                     "common.retry", "common.demoMode", "farmer.noRequests"]) {
      expect(t(k, "hi")).not.toBe(k);
    }
  });

  it("falls back to Hindi rather than showing a raw key", () => {
    expect(t("app.name", "fr")).toBe(t("app.name", "hi"));
  });

  it("returns the key itself for a genuinely unknown string", () => {
    expect(t("no.such.key", "hi")).toBe("no.such.key");
  });

  it("translates every transport status", () => {
    for (const s of ["DRAFT", "REQUESTED", "MATCHED", "IN_TRANSIT",
                     "AT_MANDI", "RETURN_LOAD", "COMPLETED", "CANCELLED"]) {
      expect(t(`status.${s}`, "hi")).not.toBe(`status.${s}`);
      expect(t(`status.${s}`, "en")).not.toBe(`status.${s}`);
    }
  });

  it("translates every quantity unit", () => {
    for (const u of ["kg", "bori", "quintal", "tonne"]) {
      expect(t(`unit.${u}`, "hi")).not.toBe(`unit.${u}`);
    }
  });
});
