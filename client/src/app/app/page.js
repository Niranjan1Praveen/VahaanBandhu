"use client";

/**
 * Role router.
 *
 * Sends an authenticated user to their own experience. This is a UX
 * convenience — the actual authorization happens server-side on every API call,
 * so a user who edits the URL sees an empty or 403 state, not another role's data.
 */

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { ErrorState, Loading } from "@/components/app/Shell";
import { useSession } from "@/components/providers/SessionProvider";
import { t } from "@/lib/i18n";

const HOME = {
  FARMER: "/app/farmer",
  TRUCKER: "/app/trucker",
  INPUT_DEALER: "/app/dealer",
};

export default function AppIndex() {
  const { status, user, lang, refresh } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "anon") router.replace("/signin");
    else if (status === "authed") {
      router.replace(user?.role ? HOME[user.role] : "/app/role");
    }
  }, [status, user, router]);

  if (status === "error") {
    return (
      <div className="min-h-screen bg-background p-6 text-foreground">
        <div className="mx-auto max-w-md pt-20">
          <ErrorState
            message={t("common.backendDown", lang)}
            onRetry={refresh}
            retryLabel={t("common.retry", lang)}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Loading label={t("common.loading", lang)} />
    </div>
  );
}
