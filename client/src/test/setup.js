import "@testing-library/jest-dom/vitest";
import { cleanup, configure } from "@testing-library/react";
import { afterEach, vi } from "vitest";

configure({ asyncUtilTimeout: 5000 });

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  window.localStorage.clear();
});

// next/navigation is not available outside the Next runtime.
//
// The router object must be STABLE across renders. Next's real useRouter
// returns a stable reference, and components legitimately list `router` in
// effect dependencies. Returning a fresh object each call made those effects
// re-fire every render, which looked like a component bug (a dashboard stuck
// re-loading) but was purely an artefact of the mock.
const routerMock = { push: vi.fn(), replace: vi.fn(), refresh: vi.fn(),
                     back: vi.fn(), forward: vi.fn(), prefetch: vi.fn() };
const searchParamsMock = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => routerMock,
  usePathname: () => "/",
  useSearchParams: () => searchParamsMock,
  useParams: () => ({}),
}));
