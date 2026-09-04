"use client";

/**
 * Legacy dashboard logout.
 *
 * Was a Kinde `LogoutLink`. Kinde is removed from the runtime, so this now uses
 * the application session, which clears the local identity and returns to the
 * entry screen. Kept because the legacy dealer dashboard shell still imports it.
 */

import { useRouter } from "next/navigation";

import { useSession } from "@/components/providers/SessionProvider";

function AppLogout() {
  const { signOut } = useSession();
  const router = useRouter();

  return (
    <button
      onClick={() => {
        signOut();
        router.push("/signin");
      }}
      className="text-sm text-white/70 transition hover:text-white"
    >
      Logout
    </button>
  );
}

export default AppLogout;
