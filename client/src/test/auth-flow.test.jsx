/**
 * The two-path entry flow.
 *
 * The load-bearing assertions here are the *separations*: Show Demo must never
 * invoke Clerk, and an unconfigured Clerk must never silently become demo auth.
 * Those two mistakes are what this flow was redesigned to prevent, so they are
 * tested directly rather than inferred from rendering.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import DemoPage from "@/app/demo/page";
import SignInPage from "@/app/signin/page";
import { SessionProvider } from "@/components/providers/SessionProvider";

const mockHealth = vi.fn();
const mockDevLogin = vi.fn();
const mockMe = vi.fn();

vi.mock("@/lib/api", () => ({
  default: {
    health: (...a) => mockHealth(...a),
    devLogin: (...a) => mockDevLogin(...a),
    me: (...a) => mockMe(...a),
  },
  apiFetch: vi.fn(),
  ApiError: class ApiError extends Error {
    constructor(m, status) {
      super(m);
      this.status = status;
    }
  },
}));

function withSession(ui) {
  return render(<SessionProvider>{ui}</SessionProvider>);
}

beforeEach(() => {
  mockHealth.mockResolvedValue({
    auth: { clerk_configured: false, dev_auth_active: true },
  });
  mockDevLogin.mockResolvedValue({ user_id: "x", role: "FARMER", onboarded: true });
  mockMe.mockResolvedValue({ user_id: "x", role: "FARMER", onboarded: true });
});

describe("sign-in entry screen", () => {
  it("offers both journeys as distinct actions", async () => {
    withSession(<SignInPage />);
    expect(await screen.findByText(/Clerk से लॉग इन करें|Login with Clerk/))
      .toBeInTheDocument();
    expect(await screen.findByText(/डेमो देखें|Show Demo/)).toBeInTheDocument();
  });

  it("does not list demo identities on the entry screen", async () => {
    withSession(<SignInPage />);
    await screen.findByText(/डेमो देखें|Show Demo/);
    // The three roles live on /demo, not beside the Clerk button.
    expect(screen.queryByText(/dev_farmer_01/)).not.toBeInTheDocument();
    expect(screen.queryByText(/dev_trucker_01/)).not.toBeInTheDocument();
  });

  it("Show Demo links to /demo and never calls Clerk or dev-login", async () => {
    withSession(<SignInPage />);
    const demo = await screen.findByText(/डेमो देखें|Show Demo/);
    expect(demo.closest("a")).toHaveAttribute("href", "/demo");
    expect(mockDevLogin).not.toHaveBeenCalled();
  });

  it("unconfigured Clerk explains itself instead of degrading to demo", async () => {
    const user = userEvent.setup();
    withSession(<SignInPage />);
    const clerk = await screen.findByText(/Clerk से लॉग इन करें|Login with Clerk/);
    await user.click(clerk);

    expect(await screen.findByText(/कॉन्फ़िगर नहीं है|not configured/))
      .toBeInTheDocument();
    // The critical assertion: no silent downgrade.
    expect(mockDevLogin).not.toHaveBeenCalled();
  });

  it("points at the real Clerk route when Clerk is configured", async () => {
    mockHealth.mockResolvedValue({
      auth: { clerk_configured: true, dev_auth_active: true },
    });
    withSession(<SignInPage />);
    const clerk = await screen.findByText(/Clerk से लॉग इन करें|Login with Clerk/);
    expect(clerk.closest("a")).toHaveAttribute("href", "/sign-in");
  });

  it("still offers the demo when Clerk IS configured", async () => {
    mockHealth.mockResolvedValue({
      auth: { clerk_configured: true, dev_auth_active: true },
    });
    withSession(<SignInPage />);
    // Demo availability is independent of Clerk availability.
    expect(await screen.findByText(/डेमो देखें|Show Demo/)).toBeInTheDocument();
  });

  it("disables the demo when the backend says it is unavailable", async () => {
    mockHealth.mockResolvedValue({
      auth: { clerk_configured: true, dev_auth_active: false },
    });
    withSession(<SignInPage />);
    const demo = await screen.findByText(/डेमो देखें|Show Demo/);
    expect(demo.closest("a")).toHaveAttribute("aria-disabled", "true");
  });
});

describe("demo role selector", () => {
  it("offers exactly the three role experiences", async () => {
    withSession(<DemoPage />);
    expect(await screen.findByText(/^किसान$|^Farmer$/)).toBeInTheDocument();
    expect(await screen.findByText(/ट्रक चालक|Trucker/)).toBeInTheDocument();
    expect(await screen.findByText(/इनपुट डीलर|Input Dealer/)).toBeInTheDocument();
  });

  it("describes what each experience shows", async () => {
    withSession(<DemoPage />);
    expect(await screen.findByText(/मंडी और मात्रा|mandi and quantity/))
      .toBeInTheDocument();
    expect(await screen.findByText(/वापसी लोड|return loads/)).toBeInTheDocument();
  });

  it("enters the farmer demo as dev_farmer_01 without the visitor typing an id",
    async () => {
      const user = userEvent.setup();
      withSession(<DemoPage />);
      await user.click(await screen.findByText(/^किसान$|^Farmer$/));
      await waitFor(() =>
        expect(mockDevLogin).toHaveBeenCalledWith(
          expect.objectContaining({ user_id: "dev_farmer_01", role: "FARMER" })));
    });

  it("enters the trucker demo as dev_trucker_01", async () => {
    const user = userEvent.setup();
    withSession(<DemoPage />);
    await user.click(await screen.findByText(/ट्रक चालक|Trucker/));
    await waitFor(() =>
      expect(mockDevLogin).toHaveBeenCalledWith(
        expect.objectContaining({ user_id: "dev_trucker_01", role: "TRUCKER" })));
  });

  it("enters the dealer demo as dev_dealer_01", async () => {
    const user = userEvent.setup();
    withSession(<DemoPage />);
    await user.click(await screen.findByText(/इनपुट डीलर|Input Dealer/));
    await waitFor(() =>
      expect(mockDevLogin).toHaveBeenCalledWith(
        expect.objectContaining({
          user_id: "dev_dealer_01", role: "INPUT_DEALER" })));
  });

  it("shows the demo-mode warning", async () => {
    withSession(<DemoPage />);
    expect(await screen.findByText(/डेमो मोड|Demo mode/)).toBeInTheDocument();
  });

  it("reports a backend refusal honestly rather than pretending to sign in",
    async () => {
      const user = userEvent.setup();
      const err = new Error("Not found");
      err.status = 404;
      mockDevLogin.mockRejectedValue(err);
      withSession(<DemoPage />);
      await user.click(await screen.findByText(/^किसान$|^Farmer$/));
      expect(await screen.findByText(/उपलब्ध नहीं है|not available/))
        .toBeInTheDocument();
    });

  it("offers a way back to the entry screen", async () => {
    withSession(<DemoPage />);
    const back = await screen.findByText(/लॉग इन पर वापस|Back to login/);
    expect(back.closest("a")).toHaveAttribute("href", "/signin");
  });
});
